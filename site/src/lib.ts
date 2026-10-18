import distribution from '../../dist-data/dictionary.json';
import registry from '../../data/sources.json';
import taxonomy from '../../data/fields.json';
export const entries=distribution.entries;
export const sourceRegistry=registry.sources;
export const fieldList=taxonomy.fields;
export const toHref=(value='')=>`${import.meta.env.BASE_URL}${value}`.replace(/\/+/g,'/');
export const firstSentence=(value:string)=>value.match(/^.*?[.!?](?=\s|$)/)?.[0] || value;

export const entryReferences=distribution.references;

export const dropped=distribution.dropped;
export const statusCounts=distribution.status_counts;
export const readerModels=distribution.reader_models;
export const reviewLabel=(entry:any)=>entry.status==='candidate'?'Candidate: drafted from the sources shown, not yet read by the two reviewers.':entry.status==='reviewed'?'Reviewed: one independent reader; copy check clear.':entry.status==='judged'?'Judged: two independent readers; copy check clear.':'Dropped: reason recorded.';
