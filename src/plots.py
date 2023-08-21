from typing import Dict, List, Optional


from matplotlib import pyplot as plt
from matplotlib import ticker
import numpy as np
import pandas as pd
import seaborn as sns


def plot_single_time_series(results, n_sims, years, title, fill: bool = True):
    for n in range(0, n_sims):
        plt.plot(years, results[n])
    if fill == True:
        min_vals = results.min(axis=1)
        max_vals = results.max(axis=1)
        plt.fill_between(years, min_vals, max_vals, alpha = 0.2)
    plt.xlabel("Years")
    plt.ylabel("Amount")
    plt.title(title)
    plt.show()


def plot_time_series(
        simulation_results,
        years,
        fill: bool = True,
        div_factor: int = 1_000_000,
):
    n_plots = len(simulation_results)
    fig, axs = plt.subplots(n_plots,1, sharex=True, figsize=(10.5,n_plots*2))

    for i, sim_name in enumerate(simulation_results.keys()):
        portfolio_balance = simulation_results[sim_name]['traditional_balance'] + simulation_results[sim_name]['roth_balance']
        portfolio_balance = portfolio_balance / div_factor
        portfolio_df = pd.DataFrame(portfolio_balance, columns=range(portfolio_balance.shape[1]))
        portfolio_df.insert(0, 'years', years)
        portfolio_df = portfolio_df.melt(id_vars='years')
        axs[i].yaxis.set_major_formatter(ticker.StrMethodFormatter('${x:,.0f}'))
        axs[i].set_title(sim_name.replace('\n', ' '))
        axs[i].set_ylabel(f'Balance, in ${div_factor:,.0f}')
        
        g = sns.lineplot(portfolio_df, x='years', y='value', hue='variable', ax=axs[i], palette=sns.color_palette(n_colors=portfolio_balance.shape[1]), legend=None)
        
        if fill == True:
            min_vals = portfolio_balance.min(axis=1)
            max_vals = portfolio_balance.max(axis=1)
            g.fill_between(years, min_vals, max_vals, alpha = 0.2)
    
    axs[i].set_xlabel('Years')
    
    fig.tight_layout()


def plot_ending_balance_hist(
    simulation_results: Dict[str, np.ndarray],
    n_sims: int,
    start_age: int,
    end_age: int,
    div_factor: float = 1_000_000.,
    bin_width: float = 0.5,
    xmin: float = 0,
    xmax: float = 30,
    lines_to_show: Optional[List[str]] = None,
):
    n_plots = len(simulation_results)
    fig, axs = plt.subplots(n_plots,1, sharex=True, sharey=True, figsize=(10.5,n_plots*2))
    
    bin_max = 0
    for sim_result in simulation_results.values():
        bin_max = max(bin_max, sim_result.max() / div_factor)
    
    bins = np.arange(0,bin_max + bin_width, bin_width)
        
    for i, sim_name in enumerate(simulation_results.keys()):
        
        axs[i].xaxis.set_major_formatter(ticker.StrMethodFormatter('${x:,.0f}'))
        axs[i].set_ylabel(sim_name)
#         axs[i].tick_params(left=False)
        axs[i].set_yticks([])
        
#         sns.histplot(simulation_results[sim_name]/div_factor, ax=axs[i], binwidth=bin_width, kde=True)
        sns.histplot(simulation_results[sim_name]/div_factor, ax=axs[i], bins=bins, kde=True)

    axs[i].set_xlabel(f'Ending balance, in ${div_factor:,.0f}')

    fig.suptitle((
        f'Ending balance of Portfolio at age {end_age}\n'
        f'Starting age {start_age} ({end_age-start_age+1}-yr period), {n_sims:,} simulations'
    ))
    fig.tight_layout()
    

    min_xlim, max_xlim, min_ylim, max_ylim = axs[0].axis()
    axs[0].axis(xmin=xmin, xmax=xmax, ymax=max_ylim*1.2)
    min_xlim, max_xlim, min_ylim, max_ylim = axs[0].axis()
    
    for i, sim_name in enumerate(simulation_results.keys()):
        
        sub_lines = {
            'Low': simulation_results[sim_name].min()/div_factor,
            '5%': np.quantile(simulation_results[sim_name], .05)/div_factor,
            '10%': np.quantile(simulation_results[sim_name], .10)/div_factor,
            'Mode': bins[np.argmax(np.bincount(np.digitize(simulation_results[sim_name]/div_factor, bins)))] - bin_width/2,
            '25%': np.quantile(simulation_results[sim_name], .25)/div_factor,
            'Median': np.median(simulation_results[sim_name])/div_factor,
            'Mean': simulation_results[sim_name].mean()/div_factor,
            '75%': np.quantile(simulation_results[sim_name], .75)/div_factor,
            '90%': np.quantile(simulation_results[sim_name], .90)/div_factor,
            '95%': np.quantile(simulation_results[sim_name], .95)/div_factor,
            'High': simulation_results[sim_name].max()/div_factor,
        }
        
        if lines_to_show is None:
            lines_to_show = sub_lines.keys()
        for j, l_name in enumerate(lines_to_show):
            l_val = sub_lines[l_name]
            axs[i].axvline(min(l_val, max_xlim), color='k', linestyle='dashed', linewidth=1)
            axs[i].text(min(l_val, xmax-0.1)+ 0.1, max_ylim*(1-(0.09*(j+1))), f'{l_name}: ${l_val:.2f}')
#             axs[i].text(min(l_val, (xmax-xmin)*.8 + xmin)+ 0.1, max_ylim*(1-(0.09*(j+1))), f'{l_name}: ${l_val:.2f}')
    
    return fig, axs