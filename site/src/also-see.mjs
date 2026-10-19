export function relatedEntries(id, index, graph) {
  return (graph.links[id] || []).map(({to}) => {
    const entry = index.get(to);
    if (!entry) throw new Error(`Unpublished see-also target: ${to}`);
    return entry;
  });
}
