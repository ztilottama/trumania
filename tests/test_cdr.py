from __future__ import division

import time
from datetime import datetime
import json

from bi.ria.generator.action import *
from bi.ria.generator.attribute import *
from bi.ria.generator.clock import *
from bi.ria.generator.circus import *
from bi.ria.generator.product import *
from bi.ria.generator.random_generators import *
from bi.ria.generator.relationship import *
from bi.ria.generator.util_functions import *
from bi.ria.generator.operations import *

from bi.ria.generator.actor import *


def compose_circus():
    """
        Builds a circus simulating call, mobility and topics.
        See test case below
    """

    ######################################
    # Define parameters
    ######################################
    tp = time.clock()
    print "Parameters"

    seed = 123456
    n_customers = 1000
    n_cells = 100
    n_agents = 100
    average_degree = 20

    prof = pd.Series([5., 5., 5., 5., 5., 3., 3.],
                     index=[timedelta(days=x, hours=23, minutes=59, seconds=59) for x in range(7)])
    time_step = 60

    mov_prof = pd.Series(
        [1., 1., 1., 1., 1., 1., 1., 1., 5., 10., 5., 1., 1., 1., 1., 1., 1., 5., 10., 5., 1., 1., 1., 1.],
        index=[timedelta(hours=h, minutes=59, seconds=59) for h in range(24)])

    cells = ["CELL_%s" % (str(i).zfill(4)) for i in range(n_cells)]
    agents = ["AGENT_%s" % (str(i).zfill(3)) for i in range(n_agents)]

    products = ["VOICE", "SMS"]

    print "Done"

    ######################################
    # Define clocks
    ######################################
    tc = time.clock()
    print "Clock"
    the_clock = Clock(datetime(year=2016, month=6, day=8), time_step, "%d%m%Y %H:%M:%S", seed)
    print "Done"

    ######################################
    # Define generators
    ######################################
    tg = time.clock()
    print "Generators"
    msisdn_gen = MSISDNGenerator("msisdn-tests-1", "0032", ["472", "473", "475", "476", "477", "478", "479"], 6, seed)
    activity_gen = GenericGenerator("user-activity", "pareto", {"a": 1.2, "m": 10.}, seed)
    timegen = WeekProfiler(time_step, prof, seed)

    mobilitytimegen = DayProfiler(time_step, mov_prof, seed)
    networkweightgenerator = GenericGenerator("network-weight", "pareto", {"a": 1.2, "m": 1.}, seed)

    mobilityweightgenerator = GenericGenerator("mobility-weight", "exponential", {"scale": 1.})

    agentweightgenerator = GenericGenerator("agent-weight", "exponential", {"scale": 1.})

    SMS_price_generator = GenericGenerator("SMS-price", "constant", {"a": 10.})
    voice_duration_generator = GenericGenerator("voice-duration", "choice", {"a": range(20, 240)}, seed)
    voice_price_generator = ValueGenerator("voice-price", 1)

    print "Done"

    ######################################
    # Initialise generators
    ######################################
    tig = time.clock()
    print "initialise Time Generators"
    timegen.initialise(the_clock)
    mobilitytimegen.initialise(the_clock)
    print "Done"

    ######################################
    # Define Actors, Relationships, ...
    ######################################
    tcal = time.clock()
    print "Create callers"
    customers = Actor(n_customers)
    print "Done"

    customers.add_attribute(name="MSISDN",
                            attr=Attribute(ids=customers.ids,
                                           init_values_generator=msisdn_gen))

    tatt = time.clock()
    # customers.gen_attribute("activity", activity_gen)
    # customers.gen_attribute("clock", timegen, weight_field="activity")

    print "Added atributes"
    tsna = time.clock()
    print "Creating social network"
    social_network_values = create_er_social_network(customer_ids=customers.ids,
                                              p=average_degree / n_customers,
                                              seed=seed)
    tsnaatt = time.clock()
    print "Done"

    ###
    # social network

    social_network = Relationship(name="neighbours",
                                  seed=seed)

    # TODO: make this a add_weighted_relations, passing the arguments to
    # build th
    social_network.add_relations(from_ids=social_network_values["A"].values,
                          to_ids=social_network_values["B"].values,
                          weights=networkweightgenerator.generate(len(
                             social_network_values.index)))

    social_network.add_relations(from_ids=social_network_values["B"].values,
                          to_ids=social_network_values["A"].values,
                          weights=networkweightgenerator.generate(len(
                             social_network_values.index)))

    print "Done SNA"
    tmo = time.clock()


    print "Network created"
    tmoatt = time.clock()


    ###
    # MSISDN -> Agent

    agent_df = pd.DataFrame.from_records(
        make_random_bipartite_data(customers.ids, agents, 0.3, seed),
        columns=["A", "AGENT"])

    print "Agent relationship created"
    tagatt = time.clock()
    agent_rel = AgentRelationship(name="people's agent",
                                  seed=seed)

    agent_rel.add_relations(from_ids=agent_df["A"],
                            to_ids=agent_df["AGENT"],
                            weights=agentweightgenerator.generate(len(
                                agent_df.index)))

    # customers's account
    recharge_trigger = TriggerGenerator(name="Topup",
                                        gen_type="logistic",
                                        parameters={},
                                        seed=seed)

    recharge_init = GenericGenerator(name="recharge init",
                                     gen_type="constant",
                                     parameters={"a": 1000.},
                                     seed=seed)

    main_account = StockAttribute(ids=customers.ids,
                                  trigger_generator=recharge_trigger,
                                  init_values_generator=recharge_init)

    customers.add_attribute(name="MAIN_ACCT", attr=main_account)

    print "Done all customers"

    tci = time.clock()
    print "Creating circus"
    flying = Circus(the_clock)

    topup = AttributeAction(name="topup",
                            actor=customers,
                            attr_name="MAIN_ACCT",

                            actorid_field_name="A",

                            joined_fields=[
                                {"from_actor": customers,
                                 "left_on": "A",
                                 "select": ["MSISDN", "CELL"],
                                 "as": ["CUSTOMER_NUMBER", "CELL"]},
                            ],

                            time_generator=ConstantProfiler(-1),
                            activity_generator=GenericGenerator("1",
                                                                "constant",
                                                                {"a": 1.}),

                            parameters={"relationship": agent_rel,
                                        "id2": "AGENT"}
                            )

    # TODO: add the actions to the actors instead of the circus
    flying.add_action(topup)

    ####
    # calls and SMS

    voice = VoiceProduct(voice_duration_generator, voice_price_generator)
    sms = SMSProduct(SMS_price_generator)

    product_df = assign_random_proportions("A", "PRODUCT", customers.ids,
                                           products, seed)
    product_rel = ProductRelationship(products={"VOICE": voice, "SMS": sms},
                                      name="people's product",
                                      seed=seed)

    # TODO: create a contructor that accept a 2 or 3 column dataframes, with the
    # convention that 2 means from, to and expect a weight generation parameters
    # and 3 means from, to, wieghts
    product_rel.add_relations(from_ids=product_df["A"],
                              to_ids=product_df["PRODUCT"],
                              weights=product_df["weight"])
    calls = ActorAction_old(name="calls",
                            actor=customers,

                            actorid_field_name="A",

                            # this becomes 2 simple relationshipSubAction
                        # described in attribute
                        random_relation_fields=[
                            {"picked_from": social_network,
                             "as": "B",
                             "join_on": "A"
                             },
                            {"picked_from": product_rel,
                             "as": "PRODUCT",
                             "join_on": "A"
                             },
                            ],

                            #
                        # emissionOperation: select =..., joined_fields= ..,
                        # include A
                        joined_fields=[
                            {"from_actor": customers,
                             "left_on": "A",
                             "select": ["MSISDN", "CELL"],
                             "as": ["A_NUMBER", "CELL_A"],
                             },
                            {"from_actor": customers,
                             "left_on": "B",
                             "select": ["MSISDN", "CELL"],
                             "as": ["B_NUMBER", "CELL_B"],
                             },
                        ],

                            time_generator=timegen,
                            activity_generator=activity_gen,
                            )

    calls.add_impact(name="value decrease",
                     attribute="MAIN_ACCT",
                     function="decrease_stock",
                     parameters={
                         # TODO: "account value" would be more explicit here
                         # I think
                        "value": "VALUE",
                        "recharge_action":topup})

    flying.add_action(calls)

    # mobility

    print "Mobility"
    mobility = Relationship(name="people's cell location",
                            seed=seed)

    mobility_df = pd.DataFrame.from_records(
        make_random_bipartite_data(customers.ids, cells, 0.4, seed),
        columns=["A", "CELL"])

    mobility.add_relations(from_ids=mobility_df["A"],
                           to_ids=mobility_df["CELL"],
                           weights=mobilityweightgenerator.generate(len(
                              mobility_df.index)))

    # Initial mobility value (ie.e cell location)
    # => TODO: there is overlap between concern of "relation" and "transient
    # attibute", they should not be initialized separately

    cell_attr = TransientAttribute(relationship=mobility)
    customers.add_attribute(name="CELL", attr=cell_attr)

    # mobility_action = AttributeAction(name="mobility",

    #                                   actor=customers,
    #                                   attr_name="CELL",
    #                                   actorid_field_name="A",
    #                                   activity_generator=GenericGenerator("1",
    #                                                                  "constant",
    #                                                                  {"a":1.}),
    #                                   time_generator=mobilitytimegen,
    #                                   parameters={})

    mobility_action = ActorAction(
        name="mobility",

        triggering_actor=customers,
        actorid_field="A",

        operations=[
            # selects a cell
            mobility.ops.select_one(from_field="A", named_as="CELL"),

            # update the CELL attribute of the actor accordingly
            cell_attr.ops.overwrite(copy_from_field="CELL"),

            # create mobility logs
            ColumnLogger(log_id="mobility", cols=["A", "CELL"]),
        ],

        activity_gen=GenericGenerator("1", "constant", {"a": 1.}),
        time_gen=mobilitytimegen,
    )

    flying.add_action(mobility_action)

    flying.add_increment(timegen)
    tr = time.clock()

    print "Done"

    all_times = {"parameters": tc - tp,
                 "clocks": tg - tc,
                 "generators": tig - tg,
                 "init generators": tcal - tig,
                 "callers creation (full)": tmo - tcal,
                 "caller creation (solo)": tatt - tcal,
                 "caller attribute creation": tsna - tatt,
                 "caller SNA graph creation": tsnaatt - tsna,
                 "mobility graph creation": tmoatt - tmo,
                 "mobility attribute creation": tci - tmoatt,
                 "circus creation": tr - tci,
                 "tr": tr,
                 }

    return flying, all_times


def test_cdr_scenario():

    cdr_circus, all_times = compose_circus()
    n_iterations = 100

    # dataframes of outcomes are returned in the order in which the actions
    # are added to the circus
    all_topup, all_cdrs, all_mov = cdr_circus.run(n_iterations)
    tf = time.clock()

    all_times["runs (all)"] = tf - all_times["tr"]
    all_times["one run (average)"] = (tf - all_times["tr"]) / n_iterations

    print (json.dumps(all_times, indent=2))

    assert all_cdrs.shape[0] > 0
    assert "datetime" in all_cdrs.columns

    assert all_mov.shape[0] > 0
    assert "datetime" in all_mov.columns

    assert all_topup.shape[0] > 0
    assert "datetime" in all_topup.columns

    print ("""
        some cdrs:
          {}

        some mobility events:
          {}

        some topup event:
          {}

    """.format(all_cdrs.head(15).to_string(), all_mov.head().to_string(),
               all_topup.head().to_string()))

    # TODO: add real post-conditions on all_cdrs, all_mov and all_topus


