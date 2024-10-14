const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function (context, options) {
  return {
    name: 'docusaurus-proxy-plugin',
    configureWebpack(config, isServer) {
      return {
        devServer: {
          onBeforeSetupMiddleware(devServer) {
            devServer.app.use(
              '/api',
              createProxyMiddleware({
                target: 'https://multivac-api.sunholo.com',
                changeOrigin: true,
                pathRewrite: { '^/api': '' },
              })
            );
          },
        },
      };
    },
  };
};