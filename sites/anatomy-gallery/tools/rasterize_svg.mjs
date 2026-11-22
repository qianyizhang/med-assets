const {default:sharp} = await import(process.env.MODEL_SURVEY_SHARP_MODULE || 'sharp');
await sharp(process.argv[2],{density:144}).resize({width:1800,height:1800,fit:'inside'}).flatten({background:'#ffffff'}).png().toFile(process.argv[3]);
