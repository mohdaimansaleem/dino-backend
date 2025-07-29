// CORS configuration for production deployment
const corsConfig = {
  development: {
    origin: [
      'http://localhost:3000',
      'http://localhost:3001',
      'http://127.0.0.1:3000',
      'http://127.0.0.1:3001'
    ],
    credentials: true,
    optionsSuccessStatus: 200
  },
  
  production: {
    origin: [
      // Add your production frontend URLs
      process.env.FRONTEND_URL,
      `https://storage.googleapis.com/${process.env.PROJECT_ID}-dino-frontend`,
      // Add custom domain if you have one
      process.env.CUSTOM_DOMAIN,
      // Cloud Storage bucket URLs
      `https://${process.env.PROJECT_ID}-dino-frontend.storage.googleapis.com`,
      // CDN URLs if using Cloud CDN
      process.env.CDN_URL
    ].filter(Boolean), // Remove undefined values
    credentials: true,
    optionsSuccessStatus: 200,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
    allowedHeaders: [
      'Origin',
      'X-Requested-With',
      'Content-Type',
      'Accept',
      'Authorization',
      'Cache-Control',
      'X-Access-Token'
    ]
  }
};

// Get CORS configuration based on environment
const getCorsConfig = () => {
  const env = process.env.NODE_ENV || 'development';
  return corsConfig[env] || corsConfig.development;
};

module.exports = {
  corsConfig,
  getCorsConfig
};