# Automatic AI fairness assessment and mitigation
### A set of queries to be integrated into an automatic tool for fairness assessment and mitigation

All queries start with the same prefixes, reported in the following. For some queries this set may be redundant, and query-specific optimizations of these prefixes is surely possible.

```
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX core: <https://purl.org/fairops/core#>
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
