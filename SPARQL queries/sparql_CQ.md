### Given an AI application working in a specific AI context and usage scenario:
We consider an AI-enabled hiring recommendation system already deployed and actively used in practice. Rather than redesigning the system from scratch according to a fair-by-design approach, the provider aims to assess its fairness properties and, if necessary, improve
them while preserving the existing architecture. Retraining or fine-tuning the recommendation model is assumed to be impractical due to computational and organizational constraints.

A recruitment platform screening job candidates can be represented as an AI System operating in the `Application Domain` of `Human Resources`. In this context, the `AI Type of Use` corresponds to `Recommendation`, while the primary `AI Task` is a `Reasoning and Decision Making` and, in particular, `Ranking`.

#### (Q1) Which legal requirements are applicable to the considered AI context?
```SPARQL
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX core: <https://purl.org/fairops/core#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?legalRequirement ?com
WHERE {
    core:HumanResources core:triggers ?legalRequirement .
    ?legalRequirement rdfs:comment ?com
}
```


#### (Q2) Which fairness concerns are associated with the given AI type of use?
```SPARQL
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX core: <https://purl.org/fairops/core#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT  ?fc ?def
WHERE {
    ?fc rdf:type ?type .
    ?type rdfs:subClassOf* core:FairnessConcern .

    ?fc core:arisesIn core:Recommendation ;
        skos:definition ?def .
}
```
#### (Q3) Which fairness notions addess a specific concern?
```
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX core: <https://purl.org/fairops/core#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?notion ?def
WHERE {
    core:PopularItemsOverrecommended core:isAddressedWith ?notion .
    ?notion core:scientificArtifactDescription ?def.
}
```
#### (Q4) Which fairness notions conflict with a selected one?
```
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX core: <https://purl.org/fairops/core#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX indiv: <https://purl.org/fairops/indiv#>
SELECT ?conflNotion ?def
WHERE {
    indiv:StatisticalParity core:conflictsWith ?conflNotion .
    ?notion core:scientificArtifactDescription ?def.
}
```
This query is based on the `core:conflictsWith` relation which is defined as a result of SWRL rules like the following:
```
core:IndependenceFairnessNotion(?a) 
    ∧ core:SufficiencyFairnessNotion(?b) 
-> core:independenceSufficiencyConflictsWith(?a, ?b)
```
 As a consequence, in order to extract the notions conflicing with the specified one, a reasoner (e.g., HermiT reasoner in Protege) must be employed and the Drools engine must be called to materialize inferred axioms prior executing the SPARQL query. 

#### (Q5) Which fairness metrics are appropriate to a specific concern in the given AI context?
```
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX core: <https://purl.org/fairops/core#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?metric ?def
WHERE {
    core:PopularItemsOverrecommended core:isQuantifiedBy ?metric .
    ?metric skos:definition ?def.
}
```
In this query, the semantic of the relation `isQuantifiedBy` is enriched by a guideline encoded in a SWRL rule specified as follows:
```
core:arisesIn(?concern, ?typeOfUse) 
    ∧ core:isSuitableFor(?metric, ?typeOfUse) 
    ∧ core:measures(?metric, ?notion) 
    ∧ core:isAddressedWith(?concern, ?notion) 
-> core:isQuantifiedBy(?concern, ?metric).
```
In practice, this guideline connects the `Fairness Concern` with the subset of `Fairness Metric`s that can quantify it in the given `AI Tupe Of Use`. Such a subset is computed by selecting the `Fairness Metric`s that measure the `Fairness Notion`s addressing that `Fairness Concern`.

#### (Q6) Which mitigation techniques addressing a concern are operationally feasible under the available deployment constraints (no feasible retraining or fine-tuning action)?
```
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX core: <https://purl.org/fairops/core#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?mitTech ?def
WHERE {
    core:PopularItemsOverrecommended core:mitigatedWith ?mitTech .
    ?mitTech skos:definition ?def;
        rdf:type ?type .
    ?type rdfs:subClassOf* ?rootMitTech .

    FILTER(
        ?rootMitTech IN (
            core:GreyBoxScores,
            core:BlackBoxDecisionOnly,
            core:HumanOversightMitigation
        )
    )
}
```
In this query too, the semantic of the relation `mitigatedWith` is enriched by a guideline encoded in a SWRL rule specified as follows:
```
core:isQuantifiedBy(?concern, ?metric) 
∧ core:enforces(?mitTech, ?metric) 
-> core:mitigatedWith(?concern, ?mitTech).
```
In practice, this connects the `Fairness Concern` with the subset of `Mitigation Technique`s that can mitigate it based on the `Fairness Metric`s that quantify that concern. 


#### (Q7) Which evidence artifacts are required to support compliance and auditing?
```
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX core: <https://purl.org/fairops/core#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?evidenceArtifact ?def
WHERE {
    core:PopularItemsOverrecommended core:requires ?evidenceArtifact .
    ?evidenceArtifact skos:definition ?def.
}
```