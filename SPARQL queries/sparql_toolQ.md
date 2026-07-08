# Automatic AI fairness assessment and mitigation
### A set of queries to be integrated into an automatic tool for fairness assessment and mitigation

All queries start with the same prefixes, reported in the following. For some queries this set may be redundant, and query-specific optimizations of these prefixes is surely possible.

```
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX core: <https://purl.org/fairops/core#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
```

We start by considering the inputs. The user is requested to select `Application Domain`, `AI Type of Use` and `AI Task` of her AI system. Hence, the first thing we need is a query to extract the possible values of these fields. The user will select the best ones to describe its application.

#### Get all available `Application Domain`s
```SQL
SELECT ?individual
WHERE {
    ?individual rdf:type core:ApplicationDomain .
}
```
#### Get all available `AI Tasks`s
```SQL
SELECT ?individual
WHERE {
    ?individual rdf:type ?type .
    ?type rdfs:subClassOf* core:AITask .
}
```
As `AITask`s are grouped into two subclasses (`Learning And Perception` and `Reasoning And Decision Making`), one may want to get the individuals together with the subclass they belong. In that case, the query is:

```SQL
SELECT ?individual ?subclass
WHERE {
    ?individual rdf:type ?subclass .
    ?subclass rdfs:subClassOf* core:AITask .
}
```

#### Get all available `AITypeOfUse`s
```SQL
SELECT ?individual 
WHERE {
    ?individual rdf:type core:AITypeOfUse .
}
```

The following thinks to be taken into account for our purpose are the resource constraints: i.e., do we have access to the training dataset? can we generate other data? Do we have the computing power to fully retring the system? etc. Depending on the answers to these questions we may want to query the ontology to get different subtrees of the `Mitigation technique` class. Here's an example of query we may want to perform:

#### Get all available `Mitigation technique`s of a given subclass

```SQL
SELECT ?individual ?subclass
WHERE {
    ?individual rdf:type ?subclass .
    ?subclass rdfs:subClassOf* core:DataGeneration .
}
```
Just as `AITask`s, `Mitigation technique`s are arranged in a tree of subclasses. The previous query retrives the individuals of mitigation techniques of class (D), together with the subclass they belong to (i.e., `SyntheticData`, `TargetedCollections`, etc. ).

Note that the name of the class `core:DataGeneration` does not report the indication of the capitalized letter (D) which is present in the resource-aware mitigation taxonomy. That letter is only reported in the `rdfs:label` of the class. So, if we want to get the same individuals as before using the label of the class `core:DataGeneration`, we need to do:

```SQL
SELECT ?individual ?subclass
WHERE {
    ?rootClass rdfs:label "Data Acquisition/Generation (D)"@en .

    ?individual rdf:type ?subclass .
    ?subclass rdfs:subClassOf* ?rootClass .
}
```

At this point, the next step is retriving the relevant/appopriate metrics and mitigation techniques for the given setting. This needs to be done through the bridge entity: `Fairness Concern`.
In other words, before retriving the metrics, we need to first query the ontology to get all relevan fairness concerns in the given `AI Type Of Use` (in this case we consider the `AI Type Of Use` of `Recommendation`):

```SQL
SELECT  ?fc 
WHERE {
    ?fc rdf:type ?type .
    ?type rdfs:subClassOf* core:FairnessConcern .

    ?fc core:arisesIn core:Recommendation.
}
```

If needed, the concern can be extracted together with its description as follows:

```SQL
SELECT  ?fc ?def
WHERE {
    ?fc rdf:type ?type .
    ?type rdfs:subClassOf* core:FairnessConcern .

    ?fc core:arisesIn core:Recommendation ;
        skos:definition ?def .
}
```

Once `FairnessConcern`s have been extracted, we can get all `FairnessNotion`s connect to each concern in this way (let's consider the concern called `BiasPerpetuation`):
```SQL
SELECT ?notion 
WHERE {
    core:BiasPerpetuation core:isAddressedWith ?notion .
}
```

Something more elaborate (and perhaps useful) would be to get alla notions relevant in the specific `AI Type Of Use` with the indication of the concerns addressef by each one:

```SQL
SELECT ?notion (GROUP_CONCAT(STR(?concern); separator=", ") AS ?concerns)
WHERE {
    ?concern rdf:type ?type .
    ?type rdfs:subClassOf* core:FairnessConcern .

    ?concern core:arisesIn core:Recommendation ;
             core:isAddressedWith ?notion .
}
GROUP BY ?notion
ORDER BY ?notion
```
Note that some parsing of the `?concerns` field may be necessary, as in this case `FairnessConcern`s are reported with their complete IRI.

#### Get references to the Legal Perspective
To focus on the legal perspective, the ontology encodes two relations: 
- ApplicationDomain ──triggers────► LegalRequirement, and
- LegalRequirement──gives rise to────►Fariness Concern

If we need to extract all `Legal Requirement`s that are triggered in the `HumanResourses` domain and give rise to the `BiasPerpetration` concern, the query would be:

```SQL
SELECT DISTINCT ?legalRequirement
WHERE {
    core:HumanResources core:triggers ?legalRequirement .

    ?legalRequirement core:givesRiseTo core:BiasPerpetuation .
}
ORDER BY ?legalRequirement
```

**NB:** At the moment, the previous query cannot retrive individuals as the `triggers` relation in not defined for any application domain. However, if we remove the first part of the query as follows, we can still retrive the `Legal Requirement`s that `givesRiseTo` the concern of `BiasPerpetuation`.

```SQL
SELECT DISTINCT ?legalRequirement
WHERE {
    ?legalRequirement core:givesRiseTo core:BiasPerpetuation .
}
ORDER BY ?legalRequirement
```

### Retriving relevant metrics

To get the relevant metrics for the given scenario, we need to intertwine the previously extracted information. In particular, we resort to the relation (`FairnessConcern`,`isQuantifiedBy`,`FairnessMetric`) and we run the following query.

```SQL
SELECT DISTINCT ?fm
WHERE {
    core:BiasPerpetuation core:isQuantifiedBy ?fm .
}
```

