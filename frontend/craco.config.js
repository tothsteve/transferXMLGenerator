const webpack = require('webpack');

module.exports = {
  webpack: {
    configure: (webpackConfig, { env, paths }) => {
      // Disable source maps in production
      if (env === 'production') {
        webpackConfig.devtool = false;
      }

      // Optimize chunks
      webpackConfig.optimization = {
        ...webpackConfig.optimization,
        splitChunks: {
          chunks: 'all',
          cacheGroups: {
            vendor: {
              test: /[\\/]node_modules[\\/]/,
              name: 'vendors',
              chunks: 'all',
            },
          },
        },
      };

      // Add progress plugin for better build feedback
      webpackConfig.plugins.push(
        new webpack.ProgressPlugin({
          activeModules: false,
          entries: true,
          modules: true,
          modulesCount: 100,
          profile: false,
          dependencies: true,
          dependenciesCount: 10000,
          percentBy: null,
        })
      );

      return webpackConfig;
    },
  },
};