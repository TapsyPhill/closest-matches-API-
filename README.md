
## Environmental Effects-Based Matching System 
:Developing a Data-Driven Pipeline for Identifying Closest 
Matches of Electrical Components to Enhance it’s Supply 
Chain Management 
Abstract: 
 
This thesis proposes a novel approach to identifying the closest matches among electrical 
components by developing a data-driven pipeline focused on environmental effects and technical 
specifications. Our goal is to enhance supply chain management by offering substitution options 
between new and existing components within the same category, improving reliability, and reducing 
downtime. The pipeline leverages a comprehensive database of electrical components, ranging from 
semiconductors and resistors to transistors to mention a few, and groups them into categories to 
ensure meaningful comparisons. 
 
Within each category, we further organize or group components by substance and detailed technical 
specifications like operating temperature, terminal finish, package shape, and DC current gain etc . 
Most importantly we hypothesize a positive relationship between substance amounts and 
environmental effects and analyze these relationships using statistical and computational techniques 
like correlation, Analysis of Variance (ANOVA), Chi-Square Test for Independence, Random forest for 
categorical correlation to identify relevant specifications for matching. Natural language processing 
and domain expertise further refine our analysis, ensuring accurate identification for relevant 
specifications for matching. 
 
 
So, methodology involves finding and filtering relevant technical specifications before matching to 
ensure only significant environmental factors are considered. Technical specifications are separated 
into numerical and categorical data types, as their matching requires different criteria. Nearest 
neighbors models and similarity scoring techniques help identify components with the closest 
environmental profiles. The pipeline, implemented using FastAPI, processes new component data 
including MPN, category name, and specifications to identify relevant matches from our database. 
The system evaluates category representation and constructs a suitable dataset to identify the 
closest matches, ultimately providing substitution options based on environmental effects. By 
aligning components through their environmental impacts, this pipeline offers supply chain 
managers a powerful tool for substitution, ensuring customers receive accurate matches, improving 
supply chain efficiency, and reducing disruptions caused by unavailable components.
