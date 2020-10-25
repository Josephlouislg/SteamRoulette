/* eslint-disable import/no-commonjs */

module.exports = (api) => {
    api.cache(true);

    const config = {
        presets: [
            [
                '@babel/preset-env', {
                    modules: false,
                    useBuiltIns: 'entry',
                    corejs: { version: 3 },
                    targets: [
                        '> 0.1% in my stats',
                        'not dead'
                    ]
                }
            ],
            '@babel/preset-react'
        ]
    };

    return config;
};
