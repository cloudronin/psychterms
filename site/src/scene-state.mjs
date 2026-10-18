// No scenario text or mockup story belongs in this module.
export const RISK_NOTICE = 'No scene is provided for this risk term.';
export function sceneState(entry) {
  if (entry.risk === true) return 'risk';
  if (!entry.vignette) return 'none';
  const scene = entry.vignette;
  // Presentation guard only. Publication still requires the reviewed data importer.
  if (!/^p_[a-z0-9_-]+$/.test(scene.card_id || '') ||
      !/^sha256:[a-f0-9]{64}$/.test(scene.card_hash || '') ||
      !/^[a-f0-9]{40}$/.test(scene.builder_commit || '') ||
      typeof scene.text !== 'string' || !scene.text.trim() ||
      typeof scene.notice !== 'string' || !scene.notice.trim()) {
    throw new Error('A scene requires unbound-card provenance and text');
  }
  return 'scene';
}
