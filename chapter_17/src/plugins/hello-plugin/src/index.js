// src/index.js

/**
 * OpenClaw 2026.3 looks for a named export called 'activate' 
 * if it doesn't find the SDK wrapper.
 */
export const activate = async (context) => {
    const { logger } = context;
    
    logger.info("**************************************************");
    logger.info("🤖 邓侃: `hello-plugin` is now ACTIVE! 成功上线！");
    logger.info("Successfully bypassed SDK with named export.");
    logger.info("**************************************************");

    // This is where you'd register tools or hooks later
};

/**
 * Some internal versions of the gateway use 'register' as a fallback.
 * We export both to be 100% safe.
 */
export const register = activate;

// We also keep a default export just in case
export default { activate };