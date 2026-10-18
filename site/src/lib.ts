import distribution from '../../dist-data/dictionary.json';
import registry from '../../data/sources.json';
import taxonomy from '../../data/fields.json';
export const entries=distribution.entries;
export const sourceRegistry=registry.sources;
export const fieldList=taxonomy.fields;
export const toHref=(value='')=>`${import.meta.env.BASE_URL}${value}`.replace(/\/+/g,'/');
export const firstSentence=(value:string)=>value.match(/^.*?[.!?](?=\s|$)/)?.[0] || value;

export const entryReferences=distribution.references;
