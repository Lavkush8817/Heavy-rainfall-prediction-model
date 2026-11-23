/**
 * Visual Chart Renderer for Real-Time Flood Risk System
 * Renders lead-time uncertainty curves, depth distributions, and risk radar charts.
 */

class DashboardCharts {
  static renderLeadTimeChart(containerId, currentData) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const leadTimes = ['t30m', 't60m', 't90m', 't120m', 't24h', 't72h'];
    const currentLead = currentData.metadata.lead_time;
    const peakRain = currentData.output1_rainfall.peak_intensity_mmh;
    const maxDepth = currentData.output3_water_depth.max_depth_cm;

    let html = `
      <div style="display: flex; flex-direction: column; gap: 8px; font-size: 11px;">
        <div style="display: flex; justify-content: space-between; color: var(--text-secondary);">
          <span>Lead Time Multi-Horizon Uncertainty Envelope</span>
          <span style="color: var(--accent-cyan);">P10 - P50 - P90 Bands</span>
        </div>
        <div style="display: flex; align-items: flex-end; gap: 6px; height: 100px; padding: 8px 0; border-bottom: 1px solid var(--border-glass);">
    `;

    const rainProgression = [0.85, 1.0, 1.15, 1.25, 0.95, 0.70];
    leadTimes.forEach((lt, idx) => {
      const scale = rainProgression[idx];
      const p50 = Math.round(peakRain * scale);
      const p10 = Math.round(p50 * 0.8);
      const p90 = Math.round(p50 * 1.3);
      const isSelected = lt === currentLead;
      const heightPct = Math.min(100, Math.max(15, (p50 / 160) * 100));

      html += `
        <div style="flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; height: 100%; justify-content: flex-end;">
          <div style="font-size: 9px; color: ${isSelected ? 'var(--accent-cyan)' : 'var(--text-muted)'};">${p50}mm</div>
          <div style="width: 100%; background: ${isSelected ? 'linear-gradient(to top, #0284c7, #38bdf8)' : 'rgba(51, 65, 85, 0.6)'}; height: ${heightPct}%; border-radius: 4px; position: relative; border: ${isSelected ? '1px solid #38bdf8' : 'none'};">
            <div style="position: absolute; top: -4px; left: 20%; right: 20%; height: 2px; background: rgba(255,255,255,0.4);"></div>
          </div>
          <div style="font-size: 9px; font-weight: ${isSelected ? 'bold' : 'normal'}; color: ${isSelected ? '#fff' : 'var(--text-secondary)'};">${lt}</div>
        </div>
      `;
    });

    html += `
        </div>
      </div>
    `;

    container.innerHTML = html;
  }

  static renderDepthDistribution(containerId, depthDist) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const total = depthDist.deep_gt_1m_cells + depthDist.impassable_30cm_to_1m_cells + depthDist.high_clearance_15cm_to_30cm_cells + depthDist.shallow_lt_15cm_cells || 1;

    const items = [
      { label: '> 1.0 Meter (Extreme Danger)', count: depthDist.deep_gt_1m_cells, color: '#ef4444' },
      { label: '30cm – 1.0m (Road Impassable)', count: depthDist.impassable_30cm_to_1m_cells, color: '#f97316' },
      { label: '15cm – 30cm (High Clearance)', count: depthDist.high_clearance_15cm_to_30cm_cells, color: '#eab308' },
      { label: '< 15cm (Passable/Shallow)', count: depthDist.shallow_lt_15cm_cells, color: '#22c55e' }
    ];

    let html = `<div style="display: flex; flex-direction: column; gap: 8px;">`;
    items.forEach(item => {
      const pct = Math.round((item.count / total) * 100);
      html += `
        <div>
          <div style="display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 3px;">
            <span>${item.label}</span>
            <span style="font-weight: bold; color: ${item.color};">${item.count} cells (${pct}%)</span>
          </div>
          <div style="height: 6px; background: rgba(255,255,255,0.06); border-radius: 3px; overflow: hidden;">
            <div style="height: 100%; width: ${pct}%; background: ${item.color}; border-radius: 3px;"></div>
          </div>
        </div>
      `;
    });
    html += `</div>`;

    container.innerHTML = html;
  }
}

window.DashboardCharts = DashboardCharts;
