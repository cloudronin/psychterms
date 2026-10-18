import distribution from '../../dist-data/dictionary.json';
import registry from '../../data/sources.json';
import taxonomy from '../../data/fields.json';
export const entries=distribution.entries;
export const sourceRegistry=registry.sources;
export const fieldList=taxonomy.fields;
export const toHref=(value='')=>`${import.meta.env.BASE_URL}${value}`.replace(/\/+/g,'/');
export const firstSentence=(value:string)=>value.match(/^.*?[.!?](?=\s|$)/)?.[0] || value;

export const entryReferences=distribution.references;

export const reviewLabel=(entry:any)=>entry.review_status==='candidate'?'Candidate · not yet reviewed':entry.review_status==='model_passed_preview'?'Model reviewed · human review pending':entry.review_status==='accepted'?'Reviewed':'Unreviewed example';
