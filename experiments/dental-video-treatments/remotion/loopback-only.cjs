/** Container compatibility adapter: skip unavailable interface enumeration.
 * Binds only loopback; does not change system networking or renderer code.
 */
const portConfig = require('./node_modules/@remotion/renderer/dist/port-config.js');
portConfig.getPortConfig = () => ({host:'127.0.0.1',hostsToTry:['127.0.0.1']});
