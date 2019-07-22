const path = require("path");

module.exports = {
	entry: "./stopwatch/src/index.tsx",
	resolve: {
		extensions: [".ts", ".tsx", ".js"]
	},
	output: {
		path: path.join(__dirname, "/stopwatch/static/stopwatch"),
		filename: "stopwatch.min.js"
	},
	module: {
		rules: [
			{
				test: /\.tsx?$/,
				use: {
					loader: "ts-loader"
				}
			},
			{
				test: /\.scss$/,
				use: [
					{
						loader: "style-loader" // creates style nodes from JS strings
					},
					{
						loader: "css-loader",
						query: {
							modules: true,
							sourceMap: true,
							localIdentName: "[name]_[local]"
							// localIdentName: "[name]__[local]___[hash:base64:5]"
						}
					},
					{
						loader: "sass-loader" //</span> compiles Sass to CSS
					}
				]
			}
		]
	},
	plugins: [
	]
}
