const webpack = require('webpack');

module.exports = {
  webpack: {
    configure: (webpackConfig, { env, paths }) => {
      // Ultra-aggressive production optimizations
      if (env === 'production') {
        webpackConfig.devtool = false;
        
        // Reduce resolve complexity
        webpackConfig.resolve = {
          ...webpackConfig.resolve,
          symlinks: false,
          cacheWithContext: false,
        };

        // Optimize module resolution
        webpackConfig.module.rules.forEach(rule => {
          if (rule.oneOf) {
            rule.oneOf.forEach(oneOfRule => {
              if (oneOfRule.test && oneOfRule.test.toString().includes('tsx?')) {
                oneOfRule.options = {
                  ...oneOfRule.options,
                  transpileOnly: true,
                  compilerOptions: {
                    noEmit: false,
                    skipLibCheck: true,
                  }
                };
              }
            });
          }
        });
      }

      // Ultra-aggressive chunk splitting
      webpackConfig.optimization = {
        ...webpackConfig.optimization,
        splitChunks: {
          chunks: 'all',
          maxSize: 244000,
          cacheGroups: {
            default: false,
            defaultVendors: false,
            vendor: {
              name: 'vendor',
              chunks: 'all',
              test: /node_modules/,
              priority: 20
            },
            common: {
              name: 'common',
              chunks: 'all',
              minChunks: 2,
              priority: 10,
              reuseExistingChunk: true
            }
          }
        },
        removeAvailableModules: false,
        removeEmptyChunks: false,
        mergeDuplicateChunks: false,
      };

      // Remove expensive plugins
      webpackConfig.plugins = webpackConfig.plugins.filter(
        plugin => 
          plugin.constructor.name !== 'ESLintWebpackPlugin' &&
          plugin.constructor.name !== 'ForkTsCheckerWebpackPlugin'
      );

      // Add minimal progress plugin
      webpackConfig.plugins.push(
        new webpack.ProgressPlugin({
          activeModules: false,
          entries: false,
          modules: false,
          profile: false,
          dependencies: false,
        })
      );

      return webpackConfig;
    },
  },
  babel: {
    plugins: env === 'production' ? [
      ['transform-remove-console', { exclude: ['error', 'warn'] }]
    ] : []
  }
};