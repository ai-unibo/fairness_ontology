### Given an AI application working in a specific AI context:
We consider an AI-enabled hiring recommendation system. A recruitment platform screening job candidates can be represented as an AI System operating in the `Application Domain` of `Human Resources`. In this context, the `AI Type of Use` corresponds to `Recommendation`, while the primary `AI Task` is a `Reasoning and Decision Making` and, in particular, `Ranking`.

#### (Q1) Which legal requirements are applicable to the considered AI context?
```SPARQL
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX core: <https://purl.org/fairops/core#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?legalRequirement
WHERE {
    ?applicationDomain core:triggers ?legalRequirement .

    FILTER(?applicationDomain = core:HumanResources)
}
```


#### (Q1) Which fairness concerns are associated with the given AI context?
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

