"""Export signed advantages and intervals without smoothing/extrapolation."""
from pathlib import Path

def plot_results(result, output_dir='figures'):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    folder = Path(output_dir); folder.mkdir(parents=True, exist_ok=True)
    colors = {'aria-1': '#007f86', 'forte-1': '#d14c36', 'forte-enterprise-1': '#555555'}
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), constrained_layout=True)
    for ax, game in zip(axes, ('W', 'N')):
        for model, style in zip(colors, ('-', '--', ':')):
            summary = result['analysis'].get(game, {}).get(model)
            if not summary:
                continue
            x = result['grid']; y = summary['mean_advantage']
            ax.plot(x, y, style, color=colors[model], label=model)
            if game == 'W':
                sensitivity = summary['calibration_sensitivity']['s_star_range']
                if sensitivity:
                    ax.axvspan(*sensitivity, color=colors[model], alpha=.12,
                               label=model+' calibration sensitivity')
            elif model == 'aria-1':
                ax.fill_between(x, summary['lower_band'], summary['upper_band'],
                                color=colors[model], alpha=.18, label='97.5% simultaneous band')
                ci = summary['inversion']['confidence_interval']
                if ci:
                    ax.axvspan(*ci, color='#777777', alpha=.1, hatch='//')
        ax.axhline(0, color='black', linewidth=.8)
        ax.set_xlabel('Local noise scale s (dimensionless)')
        ax.set_ylabel('Signed advantage (probability / fixed-prize loss)')
        ax.set_title(('Double trine: joint vs ideal one-way' if game == 'W' else
                      'Hedging: published hedge vs attained product') + '\nLOCAL MODEL')
        ax.legend(fontsize=8)
    path = folder / (result['suite'] + '-curves.png')
    fig.savefig(path, dpi=160); plt.close(fig)
    (folder / (result['suite'] + '-alt.txt')).write_text(
        'Two panels show signed exact-instance mean advantage versus local modeled noise scale. '
        'Above zero favors the joint/hedge recipe. Below zero favors the ideal one-way reference/'
        'attained product. W crossings are deterministic; W shading is calibration sensitivity, '
        'not sampling confidence. N shading marks bootstrap bands, hatched intervals crossover sets. '
        'See JSON analysis for values, unresolved/censored statuses and negative results.', encoding='utf-8')
    return str(path)

def plot_cloud_comparison(result, anchors, output_dir='figures'):
    """Discrete cloud models beside local s=1; never infer a cloud s*."""
    import matplotlib.pyplot as plt
    folder = Path(output_dir); folder.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), constrained_layout=True)
    models = ('aria-1', 'forte-1', 'forte-enterprise-1')
    for ax, game in zip(axes, ('W', 'N')):
        for j, model in enumerate(models):
            curves = result['analysis'].get(game, {}).get(model)
            if curves and 1. in result['grid']:
                ax.scatter(j-.1, curves['mean_advantage'][result['grid'].index(1.)],
                           marker='s', color='#007f86', label='LOCAL MODEL s=1' if j == 0 else None)
            for k, anchor in enumerate(a for a in anchors if a['game'] == game and a['model'] == model):
                ci = anchor['cloud_sampling']['advantage_interval']
                ax.errorbar(j+.1, anchor['advantage'],
                            yerr=[[anchor['advantage']-ci[0]], [ci[1]-anchor['advantage']]],
                            fmt='o', color='#d14c36',
                            label='RECORDED cloud sampling 95% bounds' if j == 0 and k == 0 else None)
        ax.axhline(0, color='black', linewidth=.8)
        ax.set_xticks(range(3), models, rotation=15)
        ax.set_ylabel('Signed advantage'); ax.set_title(game+' discrete anchors; no cloud scale sweep')
        ax.legend(fontsize=8)
    path = folder / (result['suite']+'-anchors.png')
    fig.savefig(path, dpi=160); plt.close(fig)
    return str(path)
