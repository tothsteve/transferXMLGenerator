const webpack = require('webpack');

module.exports = {
  webpack: {
    configure: (webpackConfig, { env, paths }) => {
      // Disable source maps in production
      if (env === 'production') {
        webpackConfig.devtool = false;
        
        // Optimize module resolution
        webpackConfig.resolve = {
          ...webpackConfig.resolve,
          symlinks: false,
        };
      }

      // Optimize chunks for better caching
      webpackConfig.optimization = {
        ...webpackConfig.optimization,
        splitChunks: {
          chunks: 'all',
          cacheGroups: {
            vendor: {
              test: /[\\/]node_modules[\\/]/,
              name: 'vendor',
              chunks: 'all',
              priority: 10
            },
            common: {
              name: 'common',
              chunks: 'all',
              minChunks: 2,
              priority: 5,
              reuseExistingChunk: true
            }
          },
        },
      };

      // Add progress plugin for build feedback
      webpackConfig.plugins.push(
        new webpack.ProgressPlugin({
          activeModules: false,
          entries: true,
          modules: false,
          profile: false,
          dependencies: false,
        })
      );

      return webpackConfig;
    },
  },
};