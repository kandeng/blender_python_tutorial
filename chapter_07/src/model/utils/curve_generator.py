import numpy as np
from scipy.interpolate import interp1d
from scipy.special import comb as binomial_coefficient
import random

class CurveGenerator:
    """
    A class to generate and interpolate curves for riverbanks.
    """
    def __init__(self, width=10, length=20, subdivisions=(8, 18)):
        """
        Initializes the generator with terrain dimensions.
        """
        self.width = width
        self.length = length
        self.subdivisions = subdivisions

    def create_bezier_curve(self, num_deviations=10):
        deviations = self.create_deviations(num_deviations)
        curve = self.interpolate_bezier(deviations)
        return curve

    def create_bspline_curve(self, num_deviations=10):
        deviations = self.create_deviations(num_deviations)
        curve = self.interpolate_bspline(deviations)
        return curve
    


    def create_deviations(self, num_deviations=10):
        """
        Creates a single list of (x, y) points with random deviations on one or both sides.
        """
        num_points = self.subdivisions[1] + 2
        points = []
        y_values = np.linspace(-0.5 * self.length, 0.5 * self.length, num_points)

        for y in y_values:
            points.append([0.0, y])

        if num_deviations > num_points:
            num_deviations = num_points
            
        deviation_indices = random.sample(range(num_points), num_deviations)

        for i in deviation_indices:
            if random.choice([True, False]):
                points[i][0] = random.uniform(-0.5 * self.width / 2.0, -0.2 * self.width / 2.0)
            else:
                points[i][0] = random.uniform(0.2 * self.width / 2.0, 0.5 * self.width / 2.0)
        return points


    def interpolate_bezier(self, input_list):
        """Helper to interpolate a single Bezier curve."""
        control_points = np.array([p for p in input_list if p[0] != 0.0])
        if len(control_points) < 2:
            return input_list

        t_values = np.linspace(0, 1, len(input_list))
        n = len(control_points) - 1
        curve_points = np.zeros((len(t_values), 2))

        for i, t in enumerate(t_values):
            for j in range(n + 1):
                basis = binomial_coefficient(n, j) * (1 - t)**(n - j) * t**j
                curve_points[i] += basis * control_points[j]
        
        final_points = []
        original_y = [p[1] for p in input_list]
        interp_x = np.interp(original_y, curve_points[:, 1], curve_points[:, 0])

        for i in range(len(input_list)):
            final_points.append([interp_x[i], original_y[i]])

        return final_points


    def interpolate_bspline(self, input_list):
        """Helper to interpolate a single B-spline curve."""
        points = np.array(input_list)
        non_zero_points = points[points[:, 0] != 0.0]

        if len(non_zero_points) < 2:
            return points.tolist()

        x = non_zero_points[:, 1]
        y = non_zero_points[:, 0]
        
        x_full = np.concatenate(([points[0, 1]], x, [points[-1, 1]]))
        y_full = np.concatenate(([0], y, [0]))

        _, unique_indices = np.unique(x_full, return_index=True)
        x_unique = x_full[np.sort(unique_indices)]
        y_unique = y_full[np.sort(unique_indices)]

        kind = 'cubic' if len(x_unique) >= 4 else 'linear'
        f = interp1d(x_unique, y_unique, kind=kind, fill_value="extrapolate")
        
        y_new = f(points[:, 1])

        max_x = 0.75 * self.width
        min_x = -max_x
        y_new_clamped = np.clip(y_new, min_x, max_x)
        
        return [[y_new_clamped[i], points[i, 1]] for i in range(len(points))]


    def merge_lists(self, first_list, second_list):
        """
        Merges two lists of deviations into a single list representing riverbanks.
        """
        if len(first_list) != len(second_list):
            raise ValueError("Deviation lists must have the same length.")

        # Sort by y-coordinate to ensure correct pairing
        left_sorted = sorted(first_list, key=lambda p: p[1])
        right_sorted = sorted(second_list, key=lambda p: p[1])

        merged_list = []
        for l_point, r_point in zip(left_sorted, right_sorted):
            x_left = l_point[0]
            x_right = r_point[0]
            y_avg = 0.5 * (l_point[1] + r_point[1])
            merged_list.append([x_left, x_right, y_avg])
            
        return merged_list
    

    def interpolate_twin_beziers(self, merged_list):
        """
        Interpolates a merged list of bank points using Bezier curves.
        Returns two lists of points, one for each bank.
        """
        left_points = [[p[0], p[2]] for p in merged_list]
        right_points = [[p[1], p[2]] for p in merged_list]

        left_curve = self.interpolate_bezier(left_points)
        right_curve = self.interpolate_bezier(right_points)

        return left_curve, right_curve
    
    def interpolate_twin_bsplines(self, merged_list):
        """
        Interpolates a merged list of bank points using B-spline curves.
        Returns two lists of points, one for each bank.
        """
        left_points = [[p[0], p[2]] for p in merged_list]
        right_points = [[p[1], p[2]] for p in merged_list]

        left_curve = self.interpolate_bspline(left_points)
        right_curve = self.interpolate_bspline(right_points)

        return left_curve, right_curve


    def plot_curves(self, merged_deviations, bezier_curves, bspline_curves):
        """
        Plots the original deviation points and the interpolated curves for both banks.
        """
        import matplotlib.pyplot as plt
        
        deviations = np.array(merged_deviations)
        left_dev = deviations[:, 0]
        right_dev = deviations[:, 1]
        y_coords = deviations[:, 2]

        left_dev_points_x = left_dev[left_dev != 0]
        left_dev_points_y = y_coords[left_dev != 0]
        right_dev_points_x = right_dev[right_dev != 0]
        right_dev_points_y = y_coords[right_dev != 0]

        bezier_left, bezier_right = np.array(bezier_curves[0]), np.array(bezier_curves[1])
        bspline_left, bspline_right = np.array(bspline_curves[0]), np.array(bspline_curves[1])

        plt.figure(figsize=(10, 8))
        plt.scatter(left_dev_points_x, left_dev_points_y, color='red', label='Left Deviation Points', zorder=5)
        plt.scatter(right_dev_points_x, right_dev_points_y, color='maroon', label='Right Deviation Points', zorder=5)

        plt.plot(bezier_left[:, 0], bezier_left[:, 1], color='blue', label='Left Bezier Curve')
        plt.plot(bezier_right[:, 0], bezier_right[:, 1], color='cyan', label='Right Bezier Curve')

        plt.plot(bspline_left[:, 0], bspline_left[:, 1], color='green', linestyle='--', label='Left B-Spline Curve')
        plt.plot(bspline_right[:, 0], bspline_right[:, 1], color='lime', linestyle='--', label='Right B-Spline Curve')
        
        plt.title('Riverbank Curve Interpolation')
        plt.xlabel('X')
        plt.ylabel('Y')
        plt.legend()
        plt.grid(True)
        plt.show()

    @staticmethod
    def run_demo():
        """
        Runs a demonstration of the CurveGenerator.
        """
        generator = CurveGenerator(width=20, length=40, subdivisions=(10, 50))
        
        left_deviations_middle = generator.create_deviations(num_deviations=14)
        left_deviations = [(x - 0.25 * generator.width, y) for x, y in left_deviations_middle]

        right_deviations_middle = generator.create_deviations(num_deviations=28)
        right_deviations = [(x + 0.25 * generator.width, y) for x, y in right_deviations_middle]

        merged_deviations = generator.merge_lists(left_deviations, right_deviations)

        bspline_curves = generator.interpolate_twin_bsplines(merged_deviations)        
        
        # bezier_curves = generator.interpolate_twin_beziers(merged_deviations)
        bezier_curve_left_middle = generator.create_bezier_curve(num_deviations=14)
        bezier_curve_left = [(x - 0.25 * generator.width, y) for x, y in bezier_curve_left_middle]
        bezier_curve_right_middle = generator.create_bezier_curve(num_deviations=28)
        bezier_curve_right = [(x + 0.25 * generator.width, y) for x, y in bezier_curve_right_middle]
        bezier_curves = (bezier_curve_left, bezier_curve_right)

        
        generator.plot_curves(merged_deviations, bezier_curves, bspline_curves)

if __name__ == "__main__":
    CurveGenerator.run_demo()
