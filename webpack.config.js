const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const ManifestPlugin = require('webpack-manifest-plugin');
const STATIC_PATH = process.env.STATIC_PATH || './out/';
// const IS_PRODUCTION = process.env.NODE_ENV === 'production';
const IS_PRODUCTION = true;


const getOutputPath = (locale) => {
    if (locale) {
        return path.resolve(STATIC_PATH, `build/${locale}/site`);
    }
    return path.resolve(STATIC_PATH, `build/site`);
};

module.exports = (env= {}) => {
  const config = {
    entry: "./roulette/index.jsx",
    output: {
      path: getOutputPath(env.locale),
      // path: path.join(__dirname, "/dist"),
      // filename: "index_bundle.js",
      pathinfo: true,
      filename: IS_PRODUCTION ? '[name]_[chunkhash].js' : '[name].js',
      chunkFilename: IS_PRODUCTION ? '[id]_[name]_[chunkhash].js' : '[name].js',
    },
    module: {
      rules: [
        {
          test: /\.(js|jsx)$/,
          exclude: /node_modules/,
          use: {
            loader: "babel-loader"
          },
        },
        {
          test: /\.css$/,
          use: ["style-loader", "css-loader"]
        }
      ]
    },
    plugins: [
      new HtmlWebpackPlugin({
        template: "./roulette/index.html"
      }),
      // new ManifestPlugin({
      //   fileName: env.locale
      //       ? path.resolve(STATIC_PATH, `manifest/site.${env.locale}.manifest.json`)
      //       : path.resolve(STATIC_PATH, 'manifest/site.manifest.json'),
      //   publicPath: env.locale ? `build/${env.locale}/site/` : 'build/site/',
      //   basePath: env.locale ? `build/${env.locale}/site/` : 'build/site/'
      // })
    ]
  };
  return config
}