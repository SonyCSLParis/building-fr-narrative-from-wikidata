# -*- coding: utf-8 -*-
""" Converting triples/key-values to sem-friendly format """
from rdflib.namespace import RDF, RDFS
from rdflib import URIRef, Namespace, Literal, Graph, XSD


class Converter:
    """ Base class for converter"""
    def __init__(self):
        self.ns_sem = Namespace("http://semanticweb.cs.vu.nl/2009/11/sem/")
        self.ns_wd = Namespace("http://www.wikidata.org/entity/")
        self.ns_geo = Namespace("http://www.opengis.net/ont/geosparql#")
        self.geom = URIRef('http://www.openlinksw.com/schemas/virtrdf#Geometry')
        self.ns_time = Namespace("http://www.w3.org/2006/time#")
        self.ns_dbo = Namespace("http://dbpedia.org/ontology/")
        self.ns_ex = Namespace("http://example.org/")

    @staticmethod
    def is_triple_in_graph(triple, graph):
        """ Checking if triple in graph """
        return triple in graph

    @staticmethod
    def _add_label(graph, uri, label):
        graph.add((uri, RDFS.label, Literal(label)))
        return graph

    def _add_event(self, graph, event, event_label):
        """ Init event triples in graph """
        graph.add((URIRef(event), RDF.type, self.ns_sem.Event))
        return self._add_label(graph=graph, uri=URIRef(event), label=event_label)

    @staticmethod
    def _search_nested_pred(graph, sub_1, pred_1, obj_2):
        """ To avoid duplicates in the graph, e.g.
        (example= s1=Coup of 18 Brumaire, p1=sem:hasActor, o2=Napoleon)
        1)in Wikidata you extract the following triples
        (s1, p1, ex:23)
        (ex:23, rdf.value, o2)
        2) In wikipedia you extract the same information, but it's already in the graph
        so you don't add it to the graph
        ==> returns whether there is n s.t. (s1, p1, ex:n), (ex:n, rdf.value, o2)
        """
        return any(obj_2 in \
            list(graph.objects(o1, URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#value'))) \
            for o1 in list(graph.objects(sub_1, pred_1)))

    def __call__(self, graph, df_info):
        return graph


class WikidataConverter(Converter):
    """ Wikidata triple converter """
    def __init__(self):
        super().__init__()

        self.func = {
            'instance of': self._add_instance_of,
            'has effect': self._add_has_effect,
            'part of': self._add_part_of,
            'point in time': self._add_point_in_time,
            'start time': self._add_begin_ts,
            'inception': self._add_begin_ts,
            'end time': self._add_end_ts,
            'dissolved, abolished or demolished date': self._add_end_ts,
            'location': self._add_location,
            'country': self._add_location,
            'located in the administrative territorial entity': self._add_location,
            'continent': self._add_location,
            'participant': self._add_participant,
            'organizer': self._add_participant,
            'founded by': self._add_participant,
            'follows': self._add_temp_link,
            'followed by': self._add_temp_link,
            'replaces': self._add_temp_link,
            'replaced by': self._add_temp_link,
        }

        self.loc_to_wd = {
            'location': self.ns_wd.P276,
            'country': self.ns_wd.P17,
            'coordinate location': self.ns_wd.P625,
            'located in the administrative territorial entity': self.ns_wd.P131,
            'continent': self.ns_wd.P30
        }

        self.part_to_wd = {
            'participant': self.ns_wd.Q56512863,
            'organizer': self.ns_wd.P664,
            'founded by': self.ns_wd.P112,
        }

        self.temp_link_to_wd = {
            'follows': self.ns_wd.P155,
            'followed by': self.ns_wd.P156,
            'replaces': self.ns_wd.P1365,
            'replaced by': self.ns_wd.Q107995509,
        }

    @staticmethod
    def _get_variables(row):
        return URIRef(row.wd_page), URIRef(row.object), row.objectLabel, row.predicate

    def _add_instance_of(self, graph, row, counter):
        sub, obj, obj_l, _ = self._get_variables(row)
        graph.add((sub, self.ns_sem.eventType, obj))
        graph.add((obj, RDF.type, self.ns_sem.EventType))
        return self._add_label(graph=graph, uri=obj, label=obj_l), counter

    def _add_has_effect(self, graph, row, counter):
        sub, obj, obj_l, _ = self._get_variables(row)
        graph.add((sub, self.ns_wd.P1542, obj))
        graph.add((self.ns_wd.P1542, RDFS.label, Literal("has effect")))
        return self._add_label(graph=graph, uri=obj, label=obj_l), counter

    def _add_part_of(self, graph, row, counter):
        sub, obj, obj_l, _ = self._get_variables(row)
        graph.add((sub, self.ns_sem.subEventOf, obj))
        graph.add((obj, RDF.type, self.ns_sem.Event))
        return self._add_label(graph, obj, obj_l), counter

    def _add_temp_link(self, graph, row, counter):
        sub, obj, obj_l, pred = self._get_variables(row)
        graph.add((sub, self.temp_link_to_wd[pred], obj))
        graph.add((self.temp_link_to_wd[pred], RDFS.label, Literal(pred)))
        return self._add_label(graph=graph, uri=obj, label=obj_l), counter

    def _add_point_in_time(self, graph, row, counter):
        sub, _, obj_l, _ = self._get_variables(row)
        graph.add((sub, self.ns_sem.hasTimeStamp, Literal(obj_l,datatype=XSD.date)))
        return graph, counter

    def _add_begin_ts(self, graph, row, counter):
        sub, _, obj_l, _ = self._get_variables(row)
        graph.add((sub, self.ns_sem.hasBeginTimeStamp, Literal(obj_l,datatype=XSD.date)))
        return graph, counter

    def _add_end_ts(self, graph, row, counter):
        sub, _, obj_l, _ = self._get_variables(row)
        graph.add((sub, self.ns_sem.hasEndTimeStamp, Literal(obj_l,datatype=XSD.date)))
        return graph, counter

    def _add_location(self, graph, row, counter):
        sub, obj, obj_l, pred = self._get_variables(row)
        graph.add((sub, self.ns_sem.hasPlace, obj))
        graph.add((obj, RDF.type, self.ns_sem.Place))
        graph.add((obj, RDFS.label, Literal(obj_l)))
        graph.add((obj, self.ns_sem.placeType, self.loc_to_wd[pred]))
        graph.add((self.loc_to_wd[pred], RDF.type, self.ns_sem.PlaceType))
        return self._add_label(graph, self.loc_to_wd[pred], pred), counter

    def _add_participant(self, graph, row, counter):
        sub, obj, obj_l, pred = self._get_variables(row)
        if not self._search_nested_pred(
            graph=graph, sub_1=sub, pred_1=self.ns_sem.hasActor, obj_2=obj):
            counter += 1
            blank_n = self.ns_ex[f"role_inst_{str(counter)}"]
            graph.add((sub, self.ns_sem.hasActor, blank_n))
            graph.add((blank_n, RDF.type, self.ns_sem.Role))
            graph.add((blank_n, RDF.value, obj))
            graph.add((obj, RDF.type, self.ns_sem.Actor))
            graph.add((obj, RDFS.label, Literal(obj_l)))
            graph.add((blank_n, self.ns_sem.roleType, self.part_to_wd[pred]))
            graph.add((self.part_to_wd[pred], RDF.type, self.ns_sem.RoleType))
            graph = self._add_label(graph=graph, uri=self.part_to_wd[pred], label=pred)

        return graph, counter

    @staticmethod
    def _add_linked_classes(graph, subjects, pred, objects):
        for sub in subjects:
            for obj in objects:
                graph.add((URIRef(sub), pred, URIRef(obj)))
        return graph

    def __call__(self, graph, df_info, counter=0):
        helper_df = df_info[["wd_page", "eventLabel"]].drop_duplicates()
        events, event_labels = helper_df.wd_page.values, helper_df.eventLabel.values
        for index, event in enumerate(events):
            graph = self._add_event(graph, event, event_labels[index])
            curr_df = df_info[df_info.wd_page == event]

            for _, row in curr_df.iterrows():
                if row.predicate in self.func:
                    graph, counter = self.func[row.predicate](graph, row, counter)

            for (sub, obj) in [('location', 'continent'), ('country', 'continent')]:
                subjects = curr_df[curr_df.predicate == sub].wd_page.values
                objects = curr_df[curr_df.predicate == obj].wd_page.values
                graph = self._add_linked_classes(graph, subjects, self.ns_wd.P361, objects)

        return graph, counter


class WikipediaConverter(Converter):
    """ Wikipedia triple converter """
    def __init__(self):
        super().__init__()

        self.func = {
            'partof': self._add_temporal_link,
            'preceded_by': self._add_temporal_link,
            'succeeded_by': self._add_temporal_link,
            'succession': self._add_temporal_link,
            'era': self._add_temporal_link,
            'event_start': self._add_temporal_link,
            'event_end': self._add_temporal_link,
            'event_pre': self._add_temporal_link,
            'precursor': self._add_temporal_link,
            'founder': self._add_participant,
            'legislature': self._add_participant,
            'appointer': self._add_participant,
            'house1': self._add_participant,
            'house2': self._add_participant,
            'organisers': self._add_participant,
            'Participants': self._add_participant,
            'place': self._add_location,
            'location': self._add_location,
            'area': self._add_location,
        }

        self.temp_link_to_wd = {
            'partof': self.ns_sem.subEventOf,
            'preceded_by': self.ns_time.intervalMetBy,
            'succeeded_by': self.ns_time.intervalMeets,
            'succession': self.ns_time.intervalMeets,
            'era': self.ns_time.intervalDuring,
            'event_start': self.ns_time.intervalStartedBy,
            'event_end': self.ns_time.intervalFinishedBy,
            'event_pre': self.ns_time.intervalAfter,
            'precursor': self.ns_time.intervalAfter,
            'event': self.ns_sem.hasSubEvent,
        }

        self.participant_to_wd = {
            'combatant': self.ns_wd.Q1414937,
            'commander': self.ns_wd.Q11247470,
            'founder': self.ns_wd.P112,
            'legislature': self.ns_wd.Q11204,
            'appointer': self.ns_wd.P748,
            'house1': self.ns_wd.Q637846,
            'house2': self.ns_wd.Q375928,
            'organisers': self.ns_wd.P664,
            'Participants': self.ns_wd.Q56512863,
            'deputy': self.ns_wd.Q1055894,
            'leader': self.ns_wd.Q1251441

        }

        self.infobox_to_real_label = {
            "commander": "commanding officer",
            "house1": "Upper house",
            "house2": "Lower house",
            "organisers": "organizer",
            "Participants": "participant"
        }

    @staticmethod
    def _get_variables(row):
        return URIRef(row.wd_page), URIRef(row.obj_wd), row.objectLabel, row.predicate

    def _add_temporal_link(self, graph, row, counter, pred_opt=None):
        sub, obj, obj_l, pred = self._get_variables(row)
        if pred_opt:
            pred = pred_opt
        graph.add((sub, self.temp_link_to_wd[pred], obj))
        graph.add((obj, RDF.type, self.ns_sem.Event))
        return self._add_label(graph=graph, uri=obj, label=obj_l), counter

    def _add_location(self, graph, row, counter):
        sub, obj, obj_l, _ = self._get_variables(row)
        graph.add((sub, self.ns_sem.hasPlace, obj))
        graph.add((obj, RDF.type, self.ns_sem.Place))
        return self._add_label(graph, obj, Literal(obj_l)), counter

    def _add_participant(self, graph, row, counter):
        sub, obj, obj_l, pred = self._get_variables(row)
        if not self._search_nested_pred(
            graph=graph, sub_1=sub, pred_1=self.ns_sem.hasActor, obj_2=obj):
            if not pred.startswith("house"):
                pred = "".join([elt for elt in pred if not elt.isdigit()])
            counter += 1
            blank_n = self.ns_ex[f"role_inst_{str(counter)}"]
            graph = self._add_blank_node_attribute(graph, blank_n, sub, obj, obj_l, pred)

        return graph, counter

    def _add_blank_node_attribute(self, graph, blank_n, sub, obj, obj_l, pred):
        graph.add((sub, self.ns_sem.hasActor, blank_n))
        graph.add((blank_n, RDF.type, self.ns_sem.Role))
        graph.add((blank_n, RDF.value, obj))
        graph.add((obj, RDF.type, self.ns_sem.Actor))
        graph.add((obj, RDFS.label, Literal(obj_l)))
        graph.add((blank_n, self.ns_sem.roleType, self.participant_to_wd[pred]))
        graph.add((self.participant_to_wd[pred], RDF.type, self.ns_sem.RoleType))

        if pred in self.infobox_to_real_label:
            graph.add((self.participant_to_wd[pred], RDFS.label,
                       Literal(self.infobox_to_real_label[pred])))
        else:
            graph.add((self.participant_to_wd[pred], RDFS.label, Literal(pred)))
        return graph

    @staticmethod
    def get_highest_nb(values):
        """ Max nb of participants """
        if values.shape[0] > 0:
            return int(max([''.join([elt for elt in x if elt.isdigit()]) for x in values]))
        return 0

    def _add_combatant_commander_link(self, graph, df_pd, counter):
        combatants = df_pd[df_pd.predicate.str.startswith("combatant")].predicate.unique()
        commanders = df_pd[df_pd.predicate.str.startswith("commander")].predicate.unique()
        nb_comb, nb_comm = self.get_highest_nb(combatants), self.get_highest_nb(commanders)
        for i in range(1, min(nb_comb,
                              nb_comm) + 1):
            for _, row_comb in df_pd[df_pd.predicate == f"combatant{i}"].iterrows():
                sub, obj, obj_l, _ = self._get_variables(row_comb)
                if not self._search_nested_pred(
                    graph=graph, sub_1=sub, pred_1=self.ns_sem.hasActor, obj_2=obj):
                    counter += 1
                    bn_comb = self.ns_ex[f"role_inst_{str(counter)}"]
                    graph = self._add_blank_node_attribute(
                        graph, bn_comb, sub, obj, obj_l, "combatant")
                for _, row_comm in df_pd[df_pd.predicate == f"commander{i}"].iterrows():
                    sub, obj, obj_l, _ = self._get_variables(row_comm)
                    if not self._search_nested_pred(
                    graph=graph, sub_1=sub, pred_1=self.ns_sem.hasActor, obj_2=obj):
                        counter += 1
                        bn_comm = self.ns_ex[f"role_inst_{str(counter)}"]
                        graph = self._add_blank_node_attribute( \
                            graph, bn_comm, sub, obj, obj_l, "commander")
                        graph.add((bn_comb, self.ns_dbo.alongside, bn_comm))

        if nb_comb != nb_comm:
            var = "combatant" if nb_comb > nb_comm else "commander"
            for i in range(min(nb_comb, nb_comm) + 1, max(nb_comb, nb_comm) + 1):
                for _, row in df_pd[df_pd.predicate == f"{var}{i}"].iterrows():
                    sub, obj, obj_l, _ = self._get_variables(row)
                    counter += 1
                    blank_n = self.ns_ex[f"role_inst_{str(counter)}"]
                    graph = self._add_blank_node_attribute(graph, blank_n, sub, obj, obj_l, var)
        return graph, counter

    def _add_leader_deputy(self, graph, df_pd, counter):
        blank_nodes = [self.ns_ex[f"role_inst_{str(counter+i)}"] \
            for i in range(1, self.get_highest_nb(df_pd.predicate.unique()) + 1)]
        counter += len(blank_nodes)
        counter_ld = 0
        for _, row in df_pd.iterrows():
            sub, obj, obj_l, pred = self._get_variables(row)
            pred = "".join([elt for elt in pred if not elt.isdigit()])
            graph = self._add_blank_node_attribute(
                graph, blank_nodes[counter_ld], sub, obj, obj_l, pred)

            if counter_ld != len(blank_nodes) - 1:
                graph.add((blank_nodes[counter_ld],
                           self.ns_time.intervalMeets, blank_nodes[counter_ld+1]))
            counter_ld += 1
        return graph, counter

    def _add_event_pred(self, graph, df_pd, counter):
        counter_curr = 1
        for _, row in df_pd.iterrows():
            graph, counter = self._add_temporal_link(graph, row, pred_opt="event", counter=counter)

            if counter_curr != df_pd.shape[0]:
                graph.add((
                    URIRef(df_pd[df_pd.predicate == f"event{counter_curr}"].obj_wd.values[0]),
                    self.ns_time.intervalBefore,
                    URIRef(df_pd[df_pd.predicate == f"event{counter_curr+1}"].obj_wd.values[0])
                ))

            counter_curr += 1
        return graph, counter

    def __call__(self, graph, df_info, counter=0):
        helper_df = df_info[["wd_page", "eventLabel"]].drop_duplicates()
        events, event_labels = helper_df.wd_page.values, helper_df.eventLabel.values
        for index, event in enumerate(events):
            print(event)
            graph = self._add_event(graph, event, event_labels[index])
            curr_df = df_info[df_info.wd_page == event]

            for _, row in curr_df.iterrows():
                if not row.predicate.startswith("house"):
                    pred = "".join([elt for elt in row.predicate if not elt.isdigit()])
                else:
                    pred = row.predicate
                if pred in self.func:
                    graph, counter = self.func[pred](graph, row, counter)

            df_pd = curr_df[(curr_df.predicate.str.startswith("combatant")) | \
                            (curr_df.predicate.str.startswith("commander"))]
            if df_pd.shape[0] > 0:
                graph, counter = self._add_combatant_commander_link(
                    graph=graph, df_pd=df_pd, counter=counter)

            for role in ["leader", "deputy"]:
                df_pd = curr_df[curr_df.predicate.str.startswith(role)]
                if df_pd.shape[0] > 0:
                    graph, counter = self._add_leader_deputy(
                        graph=graph, df_pd=df_pd, counter=counter)

            df_pd = curr_df[(curr_df.predicate.str.startswith("event")) \
                            & (~curr_df.predicate.str.startswith("event_"))]
            if df_pd.shape[0] > 0:
                graph, counter = self._add_event_pred(graph=graph, df_pd=df_pd, counter=counter)


        return graph, counter

def init_graph():
    """ Init empty graph with namespaces"""
    graph = Graph()
    graph.bind("wd", Namespace("http://www.wikidata.org/entity/"))
    graph.bind("sem", Namespace("http://semanticweb.cs.vu.nl/2009/11/sem/"))
    graph.bind("allen", Namespace("http://www.w3.org/2006/time#"))
    graph.bind("dbo", Namespace("http://dbpedia.org/ontology/"))
    graph.bind("ex", Namespace("http://example.org/"))
    return graph

def build_graph_by_type(df_pd, save_folder, converter, c_type):
    """ Filtering graph on type of link (causal etc) (given a converter) """
    for type_link in df_pd.type.unique():
        curr_df = df_pd[df_pd.type == type_link]
        graph = init_graph()
        graph, _ = converter(graph, curr_df, 0)
        graph.serialize(destination=f"{save_folder}/{type_link}_{c_type}.ttl", format="turtle")

def build_graph_by_type_combined(df1, save_folder, converter1, c_type1,
                                 df2, converter2, c_type2):
    """ Filtering graph on type of link (causal etc) (wikipedia+wikidata) """
    for type_link in df1.type.unique():
        curr_df = df1[df1.type == type_link]
        graph = init_graph()
        graph, _ = converter1(graph, curr_df, 0)

        curr_df = df2[df2.type == type_link]
        graph, _ = converter2(graph, curr_df, 0)
        graph.serialize(
            destination=f"{save_folder}/{type_link}_{c_type1}_{c_type2}.ttl",
            format="turtle")





