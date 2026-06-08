# Project Brief: The "Sugar Trap" Market Gap Analysis

**Client:** Helix CPG Partners (Strategic Food & Beverage Consultancy)  
**Deliverable:** Interactive Dashboard, Code Notebook & Insight Presentation

### A. The Executive Summary
Analysis of 109,113 cleaned products from the Open Food Facts dataset reveals a clear "Blue Ocean" opportunity in the **Fruits & Vegetables** category, where only 2.9% of products currently sit in the High Protein / Low Sugar quadrant — the lowest penetration of any major category. Using a nutrient matrix (Sugar vs. Protein per 100g), the data confirms that the snack market is heavily clustered in the high-sugar, low-protein zone, with the healthier quadrant remaining largely untapped by manufacturers. The biggest market opportunity is in Fruits & Vegetables, specifically targeting products with **17g of protein and less than 5g of sugar** per 100g — a specification validated by the 75th-percentile performance of existing Blue Ocean products in that space. The top protein-driving ingredients in high-performing products are Soy, Milk, and Oat, providing a clear starting point for R&D formulation.

### B. Project Links
**Notebook**: The full analysis code, PDF, and HTML reports can be found in the [Google Colab](https://colab.research.google.com/drive/1Xo1n_G5EqCc3Ome87MRCQIpPPhj4b3dE?usp=sharing).

**Dashboard**: Interactive[ StreamLit Dashboard](https://the-market-gap-analysis-bn4caamcmgwkq9tuib2wgp.streamlit.app/) .

**Link to Presentation**: [Presentation](https://docs.google.com/presentation/d/1skQ1WxUWPoiBwb4DUUwja3Z-kshBkjcU/edit?usp=sharing&ouid=106337736861289344369&rtpof=true&sd=true).

### C. Technical Explanation
**Data Cleaning (Story 1)**

The raw dataset was loaded as a 500,000-row sample from the Open Food Facts gzip CSV, using tab-separation and UTF-8 encoding. Columns were narrowed to 15 relevant nutritional and categorical fields. The three most critical columns — `product_name`, `sugars_100g`, and `proteins_100g` — had high null rates (up to 77.67%)-Dropping this many rows from the dataset is illogical but  this is what the data is also telling so it had to be done- so rows missing any of these were dropped first, reducing the dataset to 109,113 rows. Biologically impossible values were then removed by enforcing a 0–100g range across all per-100g nutrient columns (sugars, proteins, fat, fiber, saturated fat, salt, carbohydrates), and energy values above 900 kcal/100g were also discarded. Finally, extreme outliers at the 99th percentile for sugar and protein were trimmed to keep the scatter plots readable without distorting the underlying distribution.

**Candidate's Choice — NutriScore Gap Analysis (Story 6)**

A NutriScore Grade Distribution analysis was added across all primary categories. NutriScore (graded A–E) is an increasingly influential front-of-pack label in EU markets that directly shapes consumer purchasing decisions. The analysis mapped letter grades to a numeric scale (A=1, E=5) and computed the average NutriScore per category, then visualised the full grade distribution as a stacked horizontal bar chart. The key finding: **Sweets** has the worst average NutriScore across all categories (5.00), meaning virtually the entire category is grade E. This was chosen as the Candidate's Choice addition because it reframes the opportunity beyond just nutrient targets — a manufacturer launching a reformulated, NutriScore A/B product in the Sweets space would have a visible, immediate on-shelf competitive advantage over every existing competitor, particularly in EU markets where the label is regulated and trusted by consumers.


