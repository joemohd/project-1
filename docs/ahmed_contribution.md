# Ahmed's Contribution

## My research questions

1. How do crash rates per 1,000 completed affordable housing units vary with the volume of completed units, across boroughs, years and construction types (new construction vs preservation)?
2. Do borough-years with more completed affordable housing units show higher fatality rates in injury crashes?

## Visualizations

- **Chart 1 — scatter plot:** Uses `borough`, `year`, `construction_type`, `completed_units`, `total_completed_units`, and `crash_rate_per_1000_units`. Each point represents a borough-year/construction-type group. It compares completed units by construction type with the borough-year crash rate per 1,000 total completed affordable units; borough is shown by color, construction type by symbol, and borough-year completion volume by marker size. Groups with fewer than 100 construction-type units are omitted.
- **Chart 2 — two-panel heatmap:** Uses `borough`, `year`, `crash_count`, `fatalities`, `severe_injuries`, `non_severe_injuries`, and `total_completed_units`. The left panel shows fatalities per 100 recorded crashes; the right panel shows completed affordable units. Both panels use the same boroughs and years, with counts and rates shown on the cells.

## Findings

**Chart 1:** Among the 41 plotted groups, the highest rate is Staten Island preservation in 2022: 324 units in that construction type, 386 total borough-year units and 151 crashes, or **391.2 crashes per 1,000 units**. The lowest rate is in the Bronx in 2024: 622 crashes and 24,472 total completed units, or **25.4 per 1,000 units**; that rate appears for both construction types because it uses the shared borough-year total. Eight construction-type groups with fewer than 100 units were excluded. The high rate in the smaller group and low rate in the largest Bronx group are consistent with a mechanical denominator effect, not evidence that preservation or construction volume caused a difference in crashes.

**Chart 2:** There is no consistent pattern that more completions accompany higher fatality rates. In 2024, the Bronx had the most completions (**24,472 units**) and a middle-of-range fatality rate (**8.4 fatalities per 100 crashes**). Staten Island had the fewest completions in each of 2024–2026 (**61, 54 and 48 units**) and the highest borough rate in each of those years (**10.5, 10.9 and 12.1 per 100 crashes**, respectively); its crash counts were **133, 138 and 91**. This may indicate years for closer examination, but the Staten Island counts are small, 2026 is partial, and the pattern does not establish a causal link.

## Limitations

- The cleaned SIRTA file has 13,751 rows; 13,310 have positive recorded injury or fatality counts, while 441 have missing injury/fatality counts and cannot be classified from those fields. The charts count crash IDs for the denominator, so they should not be described as a verified injury/fatal-only dataset.
- Chart 1's normalized rate can be mechanically high when the affordable-unit denominator is small. Its crash rate is a borough-year rate repeated for each construction type, not a construction-type-specific rate.
- Staten Island has relatively small crash counts, particularly compared with larger boroughs, making annual rates more sensitive to individual crashes.
- 2026 is a partial year in this data snapshot.
- Neither visualization controls for traffic volume, population, or other factors. The observed associations do not prove causation.

## Impact for NYC

Planners and safety initiatives can use the charts to identify borough-years that merit a closer look alongside housing completion trends. The results should be treated as descriptive signals and paired with traffic exposure, population, street design, and more complete crash data before prioritizing interventions.

## My other contributions

- [ ] Data cleaning
- [ ] Data integration
- [ ] Website parts

## Prompts used

- **Chart-creation prompt:** [Paste the original prompt beginning “My task: write 2 research questions and 2 Plotly visualizations” here.]
- **Final cleanup prompt:** [Paste the final cleanup request beginning “Final cleanup of my part of the project before I commit” here.]
