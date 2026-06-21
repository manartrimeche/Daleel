> <img src="./5mct4hgo.png"
> style="width:3.54444in;height:1.11389in" /><img src="./1z4bdpq2.png"
> style="width:8.13333in;height:11.86667in" /><img src="./hgrgb0ek.png"
> style="width:2.69167in;height:0.81243in" />**Academic**
> **Supervisor:**Dr Nizar Omheni
>
> **Professional** **Supervisor** :Ms Khalil Mekki
>
> Acknowledgments

I sincerely want to express my heartfelt appreciation to everyone who
played a role in helping

me complete this project.

My foremost thanks go to my academic supervisor, Dr. Nizar Omheni, whose
unwaver-

ing support, valuable advice, and thoughtful critiques greatly
influenced the development of

my work. His commitment inspired confidence and kept me motivated
throughout.

I also extend gratitude to my technical supervisor at DNEXT, Mr. Khalil
Mekki, for his

expert guidance and steady mentorship, which considerably improved my
technical skills.

Learning from him has been a essential part of my research journey.

I am grateful to the jury members for carefully examining my thesis and
sharing their

insightful feedback; their suggestions enabled me to enhance and polish
my work further.

Thanks also go to all the professors and staff at the Polytechnic School
of Sousse for their

continuous support and dedication, providing a strong foundation for my
progress.

Finally, I deeply appreciate the encouragement, patience, and support
from my colleagues,

family, and friends throughout this entire experience.

> i
>
> Dedication

I want to dedicate this moment to my amazing parents, Arbi and Houda.
Your unwavering

encouragement, countless sacrifices, and boundless love have been the
backbone of every-

thing I have accomplished. Your wisdom, patience, and constant support
have guided me

through each step. Every achievement I celebrate reflects your
influence; truly, I wouldn’t

be here without you.

To my wonderful sisters, Marwa, Syrine, and Amal your presence has been
a bright light

during my darkest days. You’ve given me hope, strength, and comfort when
I needed it

most. Your kindness and caring attitude inspire me daily.

To my brother, Marwene my pride, partner, and greatest cheerleader. Your
enthusiasm,

positivity, and motivation have energized my journey, making it more
joyful and resilient.

To my friends your loyalty and kindness have helped me navigate tough
times. Whether we

studied late into the night, faced doubts, or conquered obstacles, your
friendship has been a

safe haven. Knowing you believed in me means everything.

To Khairerdine, my supporter and trusted confidant you’ve been there
when I needed some-

one most. Your encouragement, advice, and trust have meant the world.
More than a friend,

you are my steady anchor and strength, and I couldn’t have succeeded
without you.

To everyone I’ve met along this path each of you has played a role in my
growth, shared

valuable lessons, and helped shape who I am today.

And finally, to myself thank you for believing, persisting, and never
giving up. Every sacri-

fice, sleepless night, challenge faced, and step taken is part of this
achievement. This isn’t

just a proof of perseverance, love, gratitude, and confidence in my own
potential.

> ii
>
> Contents

List of Acronyms ix

General Introduction 1

1 Project Overview 2

> Introduction . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . . . . . 2
>
> 1.1 Presentation of the Host Company . . . . . . . . . . . . . . . . .
> . . . . . . 2
>
> 1.2 Overview of Tax-Driven Sourcing Intelligence . . . . . . . . . . .
> . . . . . . 3
>
> 1.3 Problematic . . . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . . . . 4
>
> 1.3.1 Volume and Fragmentation of Information . . . . . . . . . . . .
> . . . 5
>
> 1.3.2 Structural and Legal Complexity . . . . . . . . . . . . . . . .
> . . . . 5
>
> 1.3.3 Inconsistency in Terminology and Classification . . . . . . . .
> . . . . 5
>
> 1.4 Project Objectives . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . . . 6
>
> 1.4.1 Accommodating Structural and Legal Complexity . . . . . . . . .
> . . 7
>
> 1.4.2 Enabling Temporal and Comparative Analysis . . . . . . . . . . .
> . . 7
>
> 1.4.3 Ensuring Scalability and Integration Readiness . . . . . . . . .
> . . . . 7
>
> 1.5 Proposed Solution . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . . . . 7
>
> 1.5.1 The Automated Data Pipeline and Dashboard System . . . . . . . .
> 8
>
> 1.5.2 AI Powered Analytical Agent for Smart Querying . . . . . . . . .
> . . 9
>
> 1.6 Project Methodology . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . . . 10
>
> 1.6.1 CRISP-DM methodology . . . . . . . . . . . . . . . . . . . . . .
> . . . 11
>
> Conclusion . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . . . . . 13

2 State of Technology and Project Pipeline 14

> Introduction . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . . . . . 14
>
> 2.1 Drawbacks of Classical AI in Tax and Trade Fields . . . . . . . .
> . . . . . . 14
>
> 2.2 System Architecture: Modular Agentic Design . . . . . . . . . . .
> . . . . . . 15
>
> 2.3 RAG : Retrieval-Augmented Generation for Regulatory Precision . .
> . . . . 16
>
> iii

Contents

> 2.3.1 RAG Data Sources . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . 16
>
> 2.3.2 Main Advantages of RAG . . . . . . . . . . . . . . . . . . . . .
> . . . 17
>
> 2.4 Data Memory : Semantic Search with FAISS and ChromaDB . . . . . .
> . . . 18
>
> 2.5 Embeddings and the Transformer: Key Components of Language
> Understanding 18
>
> 2.5.1 Embedding Models . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . 19
>
> 2.6 Optimization Infrastructure: DeepSpeed, Ollama, and LangChain . .
> . . . . 20
>
> 2.6.1 DeepSpeed . . . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . 20
>
> 2.6.2 Ollama . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . 20
>
> 2.6.3 LangChain . . . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . 21
>
> 2.7 Core Technologies and Functional Roles . . . . . . . . . . . . . .
> . . . . . . . 21
>
> Project Pipeline:implementation and evaluation . . . . . . . . . . . .
> . . . . . . . 22
>
> 2.8 Data Collection . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . . . . 22
>
> 2.8.1 International Trade Centre (ITC) API
>
> 2.8.2 FedEx API and Dnext Premium Data

. . . . . . . . . . . . . . . . . 22

. . . . . . . . . . . . . . . . . 23

> 2.8.3 Automated Web Scraping and Pipeline Orchestration . . . . . . .
> . . 24
>
> 2.8.4 Centralized Data Storage in Snowflake . . . . . . . . . . . . .
> . . . . 26
>
> 2.8.5 Feature Engineering and Unified Data Preparation . . . . . . . .
> . . 27
>
> Conclusion . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . . . . . 28

3 Agentic AI Modeling and Implementation 30

> Introduction . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . . . . . 30
>
> 3.1 Working Environment . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . . 31
>
> 3.1.1 Hardware Setup . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . 31
>
> 3.1.2 Software Setup . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . 31
>
> 3.2 Models and Techniques . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . . . 34
>
> 3.2.1 DeepSeek R1 . . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . 34
>
> 3.2.2 FAISS . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . 34
>
> 3.2.3 ChromaDB . . . . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . 36
>
> 3.2.4 LangChain . . . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . 36
>
> 3.2.5 DuckDuckGo (Web Retrieval) . . . . . . . . . . . . . . . . . . .
> . . . 37
>
> 3.2.6 DeepSeed (Agent Control Layer) . . . . . . . . . . . . . . . . .
> . . . 38
>
> 3.3 Modeling and Development Approach . . . . . . . . . . . . . . . .
> . . . . . . 39
>
> iv

Contents

> 3.4 Live Query Flow and Reasoning Pipeline . . . . . . . . . . . . . .
> . . . . . . 40
>
> 3.4.1 User Query Submission . . . . . . . . . . . . . . . . . . . . .
> . . . . . 40
>
> 3.4.2 Semantic Embedding Generation
>
> 3.4.3 Vector Similarity Search (FAISS)

. . . . . . . . . . . . . . . . . . . . 40

. . . . . . . . . . . . . . . . . . . . 40

> 3.4.4 Optional Web Augmentation (DuckDuckGo) . . . . . . . . . . . . .
> . 41
>
> 3.4.5 Prompt Assembly (LangChain) . . . . . . . . . . . . . . . . . .
> . . . 41
>
> 3.4.6 Reasoning and Response Generation (DeepSeek R1 via Ollama) . . .
> 42
>
> 3.4.7 Answer Presentation and Debugging Transparency . . . . . . . . .
> . 43
>
> 3.4.8 Dataset Ingestion and Index Update . . . . . . . . . . . . . . .
> . . . 43
>
> 3.5 Validation and Interactive Deployment . . . . . . . . . . . . . .
> . . . . . . . 43
>
> 3.6 Model Evaluation . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . . . 45
>
> 3.6.1 Retrieval Pipeline Evaluation
>
> 3.6.2 Semantic Memory Evaluation

. . . . . . . . . . . . . . . . . . . . . . 45

. . . . . . . . . . . . . . . . . . . . . . 46

> 3.6.3 Practical Demonstrations and Actual Behavior of the Agent . . .
> . . 46
>
> 3.7 Interactive Analytics and Visual Data Exploration . . . . . . . .
> . . . . . . . 50
>
> Conclusion . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . . . . . 54

General Conclusion 56

Bibliography I

> v
>
> List of Figures
>
> 1.1 DNEXT Logo . . . . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . . 3
>
> 1.2 CRISP-DM Methodology Logo . . . . . . . . . . . . . . . . . . . .
> . . . . . 11
>
> 2.1 TAXI Agentic AI System Architecture . . . . . . . . . . . . . . .
> . . . . . . 16
>
> 2.2 RAG Architecture . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . . . 17
>
> 2.3 Transformer Language Understanding in TAXI . . . . . . . . . . . .
> . . . . . 20
>
> 2.4 International Trade Centre (ITC) Logo . . . . . . . . . . . . . .
> . . . . . . . 22
>
> 2.5 FedEx Logo . . . . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . . . 23
>
> 2.6 FedEx Data Retrieval and Integration Workflow in TAXI Platform . .
> . . . . 24
>
> 2.7 Dagster Logo . . . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . . . 25
>
> 2.8 Dagster Assets Orchestration . . . . . . . . . . . . . . . . . . .
> . . . . . . . 25
>
> 2.9 Dagster Job Extraction Pipelines . . . . . . . . . . . . . . . . .
> . . . . . . . 26
>
> 2.10 Snowflake Logo . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . . . . 26
>
> 2.11 Logical Data Structure of Snowflake within TAXI Pipeline . . . .
> . . . . . . 27
>
> 3.1 DeepSeek R1 Logo . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . . 34
>
> 3.2 FAISS Logo . . . . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . . . 35
>
> 3.3 RetrievalQA Architecture Overview . . . . . . . . . . . . . . . .
> . . . . . . . 35
>
> 3.4 ChromaDB Logo
>
> 3.5 LangChain Logo

. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 36

. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 37

> 3.6 DuckDuckGo Logo . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . . 37
>
> 3.7 DeepSeed Logo . . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . . . 38
>
> 3.8 FAISS-based Vector Similarity Workflow in TAXI Platform . . . . .
> . . . . . 41
>
> 3.9 LangChain Prompt Orchestration and Retrieval Pipeline in TAXI
> Platform . 42
>
> 3.10 Price Structure and Product Analysis from CSV Upload . . . . . .
> . . . . . 47
>
> 3.11 Tax Reasoning Example 1
>
> 3.12 Tax Reasoning Example 2

. . . . . . . . . . . . . . . . . . . . . . . . . . . . 48

. . . . . . . . . . . . . . . . . . . . . . . . . . . . 48

> vi

List of Figures

> 3.13 Duty Rate Reasoning for Armenia-USA Trade . . . . . . . . . . . .
> . . . . . 49
>
> 3.14 Web Retrieval Reasoning Example . . . . . . . . . . . . . . . . .
> . . . . . . 49
>
> 3.15 Power BI Logo . . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . . . 50
>
> 3.16 Interactive Tariff Overview Table Showing Applied Duties Across
> Countries
>
> and Products. . . . . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . . 51
>
> 3.17 Product Taxation Trends Over Time for Key Commodities. . . . . .
> . . . . . 52
>
> 3.18 Duty Regime Visualization Displaying MFN and Preferential
> Agreements. . 52
>
> 3.19 Price CNF Table: Combined Freight Costs and Tariff Impacts Across
> Origins
>
> and Countries. . . . . . . . . . . . . . . . . . . . . . . . . . . . .
> . . . . . . . 53
>
> 3.20 Line Chart of CNF Price Trends Over Time With Tax Adjustments. .
> . . . . 54
>
> vii
>
> List of Tables
>
> 2.1 Core Technologies and Functional Roles in TAXI . . . . . . . . . .
> . . . . . 21
>
> 3.1 Software Components and Their Functional Roles in the TAXI
> Platform . . 33
>
> 3.2 Retrieval Pipeline Evaluation Metrics . . . . . . . . . . . . . .
> . . . . . . . . 45
>
> 3.3 Semantic Memory Components Evaluation . . . . . . . . . . . . . .
> . . . . . 46
>
> viii
>
> List of Acronyms

TAXI Tax Intelligence

IA Artificial Intelligence

RAG Retrieval-Augmented Generation

LLM Large Language Model

CRISP-DM Cross-Industry Standard Process for Data Mining

CSV Comma-Separated Values

FAISS Facebook AI Similarity Search

GPU Graphics Processing Unit

ITC International Trade Centre

API Application Programming Interface

FedEx Federal Express

HS Harmonized System

WTO World Trade Organization

CNF Cost and Freight

JSON JavaScript Object Notation

ETL Extract, Transform, Load

FLAT Future Logic for Automated Trade (Future price and CNF)

SQL Structured Query Language

BI Business Intelligence

> ix

List of Tables

RAM Random Access Memory

DDR5 Double Data Rate 5 Synchronous Dynamic Random-Access Memory

GDDR6 Graphics Double Data Rate 6

NVME Non-Volatile Memory Express

SSD Solid-State Drive

HD Hard Disk

IPS In-Plane Switching

JSONL JSON Lines

Parquet Apache Parquet File Format

PyArrow Python Arrow Library

Regex Regular Expression

DuckDB In-Process SQL OLAP Database Management System

MFN Most-Favored Nation

> x
>
> General Introduction

Agricultural industrial trade development has caused companies to modify
their sourcing

approaches beyond basic market price calculations and taxation stands as
one of the most

vital elements. Import duty policies together with trade tariffs and
local taxation systems

determine how market competitiveness develops while also affecting
pricing methods and di-

recting border crossing procurement activities. DNEXT Intelligence SA is
the company that

initiated this project which investigates how international tax
regulations affect agricultural

product pricing strategies. The development of an intelligent system
forms the main goal

of this initiative because it must aggregate tax data while verifying it
with domestic and

international price trend analysis. The platform emerges as a high level
AI powered system

which provides immediate cost effective sourcing paths to customers.
Global supply chains

require organizations to carry out fast yet knowledgeable business
choices.

Tax data remains dificult to handle because it exists as disconnected
sources among different

jurisdictions and lacks consistent structure and is tied to constantly
moving tax regulations.

The project directly tackles system complexity by implementing automated
processes and

enhanced data engineering along with multi agent AI that produces vital
information for

import-export functions. The solution contains two essential elements
which consist of a

dynamic data collection pipeline that visualizes tax data continuously
and an advanced AI

analytical system. The agent works from DeepSeek-R1 foundation to access
strategic in-

formation flowing from a real time knowledge base constructed with RAG
and LangChain

and ChromaDB and FAISS functionalities. The combination of tax
intelligence with exist-

ing market analytics through this project enables DNEXT Intelligence SA
to supply clients

with resourceful sourcing recommendations that help them cut costs and
reduce risks while

bolstering their global market competitiveness.

> 1
>
> 1 Project Overview

Introduction

Changing trade policies together with price changes and essential
procurement demands

modify global agricultural patterns in sourcing operations. Strategic
tax policies operate

as management tools that direct transportation of products throughout
supply chains while

influencing market competition and enabling operators to find the lowest
cost approaches

throughout complete supply networks.

> This first oficial document concerning the TAXI project appears in
> this chapter. This

research examines DNEXT Intelligence SA as the main host company by
analyzing crucial

challenges discovered in the project next to price fluctuations and
operational complexities

and tax fragments. TAXI functions through AI based technology to deliver
agricultural

focused strategic sourcing tools together with basic tax information.
The chapter outlines

the approaches for development that will create operational capabilities
through this system.

1.1 Presentation of the Host Company

The enterprise DNEXT Intelligence SA operates its business from
Switzerland and Tunisia

through its headquarters in Switzerland which it established in 2020.
The company dedicates

> 2

Chapter 1. Project Overview<img src="./3sgcntfl.png"
style="width:3.24804in;height:1.02058in" />

itself to agricultural data development to help professionals across 28
nations track market

trends and identify threats throughout their essential procuring
selections.

> The DNEXT Market Data Intelligence Platform functions as a digital
> database plat-

form which enables users to view selected datasets and monitor real-time
market data while

studying interactive dashboards. The DNEXT Platform \[1\]fulfills
contemporary business

needs of commodity traders and their analyst staff and procurement team
to handle risks in

volatile agricultural markets.

> DNEXTspecializesincollectingandprovidingagriculturalproductsandweathercustoms

import-export data together with data collection and transforming
services for the technical

agra-food market. DNEXT staff retrieve appropriate data from various
sources before they

transform the information to build workable dataset collections.

> DNEXT started offering its data platform commercially in 2021 after
> developing the

platform at its facilities and now provides data service subscriptions
to business clients.

DNEXT develops its business operations by providing consulting solutions
while maintain-

ing customer support and marketing solutions to establish powerful
relationships between

partners and clients.

> Figure 1.1: DNEXT Logo

1.2 Overview of Tax-Driven Sourcing Intelligence

A complete evaluation process for international agricultural trade
products includes more

than just initial pricing information. The total landed cost represents
every single expense in-

curred to deliver a product to market although customs duties and
import-export tariffs and

logistical expenses and national and local tax rules determine its
price. The fiscal elements

which are commonly affected by political and international agreements
create substantial

changes to the way businesses conduct sourcing activities between
different territories.

> The strategic requirement to accurately determine tax implications for
> sourcing decisions
>
> 3

Chapter 1. Project Overview

has surfaced because the agri-food sector demonstrates growing
globalization alongside inten-

sified competition. Tax structures affect both the product prices of
imported goods together

with supply chain risks and procurement timing while shaping market
competitiveness. The

appearance of cheaper imports often ends up becoming unprofitable after
taxes and tariffs

are considered which leads to local products gaining preferential tax
advantages.

> The TAXI project emerged to tackle increasing business complexities.
> The main purpose

of this system entails the creation of intelligent solution which
combines various tax infor-

mation while matching it against commodity price patterns across diverse
periods of time.

The system ensures stakeholders gain detailed insights about the fiscal
impact of choosing

between domestic sources and imported products because standard price
assessments usually

neglect these factors.

> Its main purpose extends past displaying data because TAXI creates
> valuable strategic

understanding for users. The system promotes complex queries through
advanced visual-

izations and AI interpretation capabilities. The tool offers a
functionality to identify which

exporting nation provides the most cost eficient effective tax rate for
specific commodities.

> The question emerges whether importing maize as an instance would be
> more suitable

in terms of costs compared to sourcing local supplies within a certain
market segment this

quarter.

> Business operations benefit from TAXI because this project uses
> taxation analytics to

add crucial information to their procurement processes.

> DNEXT Intelligence SA utilizes the system to provide clients with
> comprehensive market

insights that integrate both pricing data and entire financial
transaction information.

> Tax sensitive sourcing information provides agri-food industry
> professionals with the

same strategic decision-making capabilities that financial data provides
corporations making

business choices.

1.3 Problematic

The assessment method of agricultural trade costs heavily depends on
taxation data al-

though researchers find this fundamental metric challenging due to trade
analysis complex-

ity. Decision makers and analysts experience significant obstacles in
obtaining meaningful

> 4

Chapter 1. Project Overview

and comparable data by reason of worldwide fractured tax systems and the
variance in for-

matting methods and unclear terminology usage. The complexity of these
factors produces

significant operational dificulties during critical decision making
processes for sourcing.

> TAXI developed its operational structure as an explicit answer to
> circulating barriers.

The project addresses core obstacles that stop organizations from
extracting effective tax

data for procurement strategy development.

1.3.1 Volume and Fragmentation of Information

Extremely large and unorganized documentation of tax related materials
creates substantial

barriers that organizations must overcome. Each country and in some
cases, each product

category applies unique rules, exemptions, and tariff structures. The
storage of tax re-

lated information by government portals and legal bulletins and customs
databases operates

without any uniform documentation standards. Slow human interpretation
of numerous

contradictory information sources leads to errors and produces
unfinished analyses of the

information.

1.3.2 Structural and Legal Complexity

The large quantity of tax data surpasses merely being high volume
because its many formats

prove dificult to interpret. The content structure of oficial
documentation varies among

jurisdictions because each region implements its specific organizational
rules and format

standards. Additionally each jurisdiction mandates distinct rules
concerning information

depth within oficial documentation. Specialists must interpret multiple
internal procedural

requirements present in these rules. Traditional analysis methods fail
to handle regulatory

content complexity because regulatory content exceeds their analytical
capabilities.

1.3.3 Inconsistency in Terminology and Classification

Tax information accessibility does not remove challenges since tax
vocabulary operates dif-

ferently between countries. Multiple trade partners hold diverse
classifications of identical

agricultural products and their taxation terminology displays distinct
meanings because of

> 5

Chapter 1. Project Overview

their separate legal frameworks which contain "tariff rebate," "duty
suspension" and "pref-

erential rate."

> Each legal context has specific interpretations for general language
> which affects its mean-

ing. The widespread differences between countries makes it dificult for
organizations to

implement automated or standardized tax analysis across regions and
commodities.

> A context aware automated system presents itself as necessary because
> tax data demon-

strates unique complexities alongside changing characteristics combined
with major opera-

tional effects. Businesses which do not employ such systems place their
sourcing strategies

at risk of making decisions from unliquidated or ancient data which may
create costly results

and regulatory headaches and market opportunity loss.

> The TAXI project addresses specific dificulties to create next
> generation agricultural

intelligence solutions that produce strategic insights from raw taxation
information.

1.4 Project Objectives

Through the TAXI project organizations obtain support in international
agricultural pro-

curement through enterprise tax solutions which unite pricing approaches
with procurement

management. The system must solve multiple issues that occur during
practical implemen-

tations when accessing and utilizing tax related information. This
developing plan for the

project maintains two primary purposes to unite technical feasibility
with business require-

ments:

> The system must process extensive information that originates from
> various information

sources. A complete data acquisition process must be implemented within
the proposed

framework to retrieve various types of heterogeneous information
networks from multiple

domestic and international sources such as regulatory documents and
commodity prices.

Real time access operations should be built into the data management
solution because it

needs to provide instant access to information as well as maintain both
data understanding

and usability during real time periods.

> 6

Chapter 1. Project Overview

1.4.1 Accommodating Structural and Legal Complexity

The system should handle data processing tasks that normalize data of
different formats

and tax language usages from different administrative areas. The
database must process

multiple document styles incorporating classification and conditional
systems because it

should function without disruptions based on law type and origin.

1.4.2 Enabling Temporal and Comparative Analysis

Workflow systems should give users access to data analysis tools which
display past and

existing tax patterns and alternative sourcing options. Users can
perform retrospective

historical pattern evaluation and fiscal forecasting through the
established system.

> The solution provides AI based solutions that adapt themselves to
> specific situations. A

computerized solution should evaluate user verbal demands to supply
factual data responses

through AI based analysis. User analytical requirements receive specific
responses through

the system because it adapts to product selection with geographical
location data combined

with time based needs and built in tax regulations.

1.4.3 Ensuring Scalability and Integration Readiness

DNEXT needs a scalable platform with modular functions that will enable
the company

to expand its business presence into diverse markets with their assorted
products and tax

systems. Integration of the system needs to perform without obstacles
within DNEXT’s

existing platform structures and data operations.

> The core goals develop the base structure of the TAXI project. The
> commitment exists to

convert basic fiscal information into operational worth through its
application which enables

improved sourcing selection and diminished tax related risks and
enhanced supply chain

transparency.

1.5 Proposed Solution

The solution brings together two linked systems for dealing with direct
tax data interpreta-

tion problems and agricultural sourcing requirements by utilizing AI
powered reasoning and

> 7

Chapter 1. Project Overview

automated information processing. Specialized logic within this system
enables it to handle

different global tax rules besides dynamic market commodity prices and
creates understand-

able insights for users.

> The project helps users obtain significant tax information at a fast
> rate and converts

complicated pricing elements into clear business insights. The TAXI
solution addresses

recognized problems to deliver stakeholders eficient platforms that let
them select low price

appropriate sources while requiring less time to make better decisions.

1.5.1 The Automated Data Pipeline and Dashboard System

The Automated Data Pipeline and Dashboard System serves as the
fundamental mechanism

for executing data processing operations. This automated pipeline is
constructed using

Python and operates on the Dagster orchestration platform. It provides
options for both

fully serverless and hybrid deployments, incorporates native branching
capabilities, features

integrated cataloging, and offers cost observability, thereby enhancing
the functionality of

orchestration solutions for users.

> The system functions as the primary controller, equipped with
> scheduling capabilities

that facilitate the execution of tasks aimed at acquiring valid data and
transforming it into

a finalized state. Through its Jobs and assets, users can visually
represent tasks, ensur-

ing that the system remains comprehensible while promoting sustainable
maintenance and

operational consistency.

> This pipeline offers users three essential functionalities:
>
> • Regular extraction of tax regulations and commodity price data from
> various interna-
>
> tional sources.
>
> • Execution of quality control tests to validate and organize incoming
> data collections.
>
> • Transformation of raw inputs into clean, standardized datasets that
> are prepared for
>
> analysis, alongside centralized storage and rapid access via local
> storage.
>
> Moreover, Dagster includes a version control system that enables
> developers to compre-

hend their workflows and maintain the stability of project systems while
accommodating

developmental needs. The scheduling features allow users to perform
backfill operations,

> 8

Chapter 1. Project Overview

thereby preserving the historical accuracy of data in conjunction with
the latest evaluation

methodologies or corrective inputs.

> After collection, the data is carefully finalized and standardized to
> ensure consistency

before being integrated into the dashboard and the Agentic AI system.
This polished data

forms the backbone for creating intuitive visual comparisons, such as
contrasting costs be-

tween local and international suppliers or assessing how different
regional tax policies impact

finances. Also, it enables smart querying, supports logical reasoning,
and assists automated

decision making within the AI platform, enhancing overall eficiency.

> The project computes total landed costs by integrating commodity data
> with geographic

factors and Incoterm specifications. Furthermore, it ensures the
availability of current data

while preserving historical records, which assist users in monitoring
fluctuations in tax ex-

posure and pricing over time.

1.5.2 AI Powered Analytical Agent for Smart Querying

The conversational artificial intelligence system is engineered to
support intricate problem

solving through a dialogue like interaction. It activates a range of
specialized agents in-

ternally, each assigned to specific tasks, which allows users to obtain
swift and accurate

responses without the need for conventional iterative exchanges.

> At the core of this system is DeepSeek-R1, which thoroughly interprets
> user inquiries and

it systematically organizes information from relevant knowledge bases
and utilizes reasoning

to produce logical and contextually appropriate solutions.

> TheinformationpipelineisfurtheraugmentedbyRetrieval-AugmentedGeneration(RAG).

For example, when presented with the inquiry, “Which supplier in North
Africa offers the

lowest net cost after tariffs?”, DeepSeek-R1 retrieves relevant
documents from our local

database (indexed in ChromaDB), extracts the necessary figures, and
delivers a concise,

evidence-based response.

> By incorporating dynamic retrieval, advanced reasoning, and on demand
> tool execution,

the platform transitions from a conventional static data repository to
an intelligent pro-

curement assistant. It identifies cost trends, performs "what-if"
analyses, and significantly

decreases evaluation times, all while enhancing accuracy and preserving
a conversational

interface throughout the process.

> 9

Chapter 1. Project Overview

> The agent elevates the TAXI system from a static data platform to a
> dynamic decision

support assistant. The system creates customized analyses that enable
users to conduct

procurement evaluations while recognizing patterns and building
scenarios thus cutting down

evaluation times while boosting accuracy.

> System Highlights and Advantages:
>
> • The TAXI system delivers its advantages through the combination of
> automated work-
>
> flows using Dagster and local data infrastructure with RAG reasoning
> powered by AI.
>
> • The system oversees complete data processing it receives in its
> collection stage and
>
> supports operations until producing useful results.
>
> • Hardware platform provides instant access to both procurement data
> comparison as
>
> well as tax expense analysis information to users.
>
> • The system delivers fast responses that identify both commodity
> market shifts and
>
> changes in fiscal measures.
>
> • Conversational querying for intuitive access to deep analytical
> intelligence.
>
> • Users gain control over dificult international procurement decisions
> through practical
>
> insights derived from tax and pricing information within the cohesive
> solution.

1.6 Project Methodology

CRISP-DM served as the fundamental design principle for TAXI by offering
standardized

project execution algorithms for the entire project duration. This data
mining approach

became widely used mainly because its flexible design combined with
organized procedures

meets the requirements of advanced data integration projects using
machine learning meth-

ods and analytic solutions.

> This process includes sequential instructions to handle entire project
> development from

understanding business needs to running the final system. The project
undertakes multiple

initial sequences because feedback leads to continuous system
transformation that matches

evolving tax regulations and varying data sources and advanced AI
components.

> 10

Chapter 1. Project Overview<img src="./xybadubm.png"
style="width:3.24795in;height:2.65706in" />

1.6.1

1.6.1.1

CRISP-DM methodology

> Overview of the CRISP-DM Approach

The initial phase of CRISP-DM \[2\]data science project lifecycles is
Business understanding

yet it serves alongside Implementation as two components from a total
six-step method. The

six developmental phases merge critical business requirements with
operational demands to

establish helpful solutions that fulfill required functions for
designated user groups.

> Figure 1.2: CRISP-DM Methodology Logo

1.6.1.2 Business problem understanding

This initial phase focuses on understanding the project goals,
objectives, and requirements

from a business perspective, then converting this knowledge into a data
mining problem

definition and a preliminary plan with a specific set of tasks and
desired outcomes to achieve

project-level objectives.

1.6.1.3 Data Understanding

The data understanding phase starts with initial data collection and
proceeds with activities

such as feature description, primary data analysis, and exploratory data
analysis that enable

you to become familiar with the data, identify the data quality problems
such as missing

values, inconsistent data entries, and/or identify compelling subsets to
form a hypothesis

regarding confidential information.

> 11

Chapter 1. Project Overview

1.6.1.4 Data Preparation

The data preparation phase covers all activities needed to construct the
final dataset fed

into the modeling tools from the initial raw data. Data preparation
tasks are likely to be

performed multiple times and not in any prescribed order. Tasks include
data table, feature

selection, feature engineering, as well as feature transformation and
cleaning of data for

modeling tools and techniques.

1.6.1.5 Modeling

In this phase, various modeling techniques depending on the problem
statement, are selected

and applied, and their parameters are calibrated to find optimal
modeling performance. Typ-

ically, there are several techniques for the same data mining problem
type. Some techniques

have specific requirements for the format of data it needs. Therefore,
going back to the data

preparation phase is often necessary at this stage.

1.6.1.6 Evaluation

The evaluation phase is one of the most crucial phases of any data
science project lifecycle.

At this stage in your project, you must have built machine learning
models. Models might

be performing well on your training data, but it is necessary to test
and evaluate it on unseen

data for the model to achieve its objectives. Appropriate evaluation
metrics are measured

and well-tested at this stage. At the end of this phase, a decision on
using the data mining

results should be reached.

1.6.1.7 Deployment

The creation of the model is generally not the end of the project. Even
if the purpose of the

model is to analyze the data and increase the understanding of the data,
the knowledge or

insight gained from the modeling needs to be presented so that the end
users of the model can

use it. End users could be operational level staff, business executives,
or customers as well.

It often involves applying live models within an organization’s decision
making processes for

example, real-time personalization web page, product recommender system,
or scoring of

marketing leads. Depending on the requirements, the deployment phase can
be as simple

> 12

Chapter 1. Project Overview

as generating a dashboard, or as complex as implementing a repeatable
data mining process

across the enterprise.

Conclusion

The concluding section of this chapter delineates the fundamental
context for our research en-

deavor. We have introduced the host organization, articulated the
primary research question,

and outlined the contributions of our study. Furthermore, we have
detailed the methodology

that will inform our analysis. In the subsequent chapter, we will
undertake a comprehen-

sive examination of contemporary technologies, critically evaluating
traditional methods,

identifying their shortcomings, and exploring recent innovations aimed
at mitigating these

challenges.

> 13
>
> 2 State of Technology and Project Pipeline

Introduction

In today’s interconnected global economy, keeping up with constantly
changing tax laws can

be quite challenging. Governments frequently update regulations, duties,
and agreements

across different countries in real time, which creates a complex and
often disconnected data

environment that’s tough to monitor manually. To help navigate this
complexity, we devel-

oped the TAXI Agentic AI an intelligent, flexible, and modular platform
designed to enable

users to quickly and accurately analyze detailed international tax
information.

This chapter explores the technical architecture and main features of
the TAXI Agentic AI.

We look into how the system is built, its data retrieval methods,
semantic search capa-

bilities, advanced language understanding, and how it optimizes
infrastructure. All these

components work together to allow TAXI to provide real-time insights,
support energetic

reasoning, and ensure compliance with developing global tax regulations.

2.1 Drawbacks of Classical AI in Tax and Trade Fields

Despite notable progress in artificial intelligence and machine
learning, traditional large

language models (LLMs) still struggle to meet the specialized needs of
the tax and trade

> 14

Chapter 2.

industries.

> State of Technology and Project Pipeline

These models often find it dificult to interpret complex regulations,
process

specialized terminology, adapt to different country specific rules,
ensure accuracy in sensitive

financial advice, and handle confidential data effectively. \[3\]

> • Static Knowledge Limitation: Because tax laws are constantly
> changing across
>
> different regions, systems trained on past data often fall behind,
> giving outdated or
>
> wrong advice unless they are regularly refreshed with new information.
>
> • Insuficient Jurisdictional Awareness: Many models also find it
> dificult to under-
>
> stand specific regional rules, exemptions, or legal subtleties that
> they weren’t trained
>
> on initially, which limits their ability to handle local legal
> environments accurately.
>
> • Challenges Handling Structured Data Formats: Also, because a lot of
> tax data
>
> is stored in structured formats like spreadsheets, CSV files, or
> databases, language
>
> models primarily designed to understand unstructured text often
> struggle to interpret,
>
> relate, or analyze tabular or numeric information.
>
> • Generation of Misleading Information (Hallucination): Sometimes,
> these mod-
>
> els may generate responses that sound confident but are actually
> incorrect, which can
>
> be risky when dealing with important legal, financial, or compliance
> issues.

2.2 System Architecture: Modular Agentic Design

The TAXI Agentic AI is designed as a modular, agent-driven system that
replicates expert-

level decision-making processes in the domain of taxation. Its
architecture integrates au-

tonomous reasoning agents, multi-source data retrieval pipelines,
continuous regulatory up-

dates, structured data ingestion, long term semantic memory, and secure
local deployment

options.

> At its core lies the multilingual language model DeepSeek-R1, which is
> responsible

for natural language understanding and generation. This central model is
supported by a

coordinated set of subsystems that enable autonomous reasoning, real
time data integration,

and transparent, verifiable outputs.

> 15

Chapter 2. State of Technology and Project
Pipeline<img src="./cgzrvukg.png"
style="width:3.24791in;height:2.96548in" />

> Figure 2.1: TAXI Agentic AI System Architecture

2.3 RAG : Retrieval-Augmented Generation for Regula-

> tory Precision

A notable breakthrough in this system is the implementation of
Retrieval-Augmented Gener-

ation (RAG) \[4\], a process that considerably changes how the AI
thinks, reacts, and explains

itself. Unlike conventional language models that only depend on the
knowledge stored dur-

ing their training which remains unchanged ,RAG enables the AI to
integrate new, relevant

information from external sources in real time. By combining RAG with
DeepSeek R1, the

model can effortlessly draw from a variety of external data to generate
more accurate and

context-aware responses.

2.3.1 RAG Data Sources

> • Local Structured Data: User uploaded files such as CSVs or Excel
> spreadsheets.
>
> • Web-Based Regulatory Data: Real time queries via DuckDuckGo for
> newly pub-
>
> lished tax rules or trade agreements.
>
> • Persistent Internal Memory: The Dnext Data Layer, a proprietary
> database cu-
>
> rated for tax intelligence.
>
> 16

Chapter 2. State of Technology and Project
Pipeline<img src="./xtyzff0y.png"
style="width:4.5471in;height:2.40535in" />

> Figure 2.2: RAG Architecture
>
> \[5\]

2.3.2 Main Advantages of RAG

> • Source Traceability: All answers are directly supported by verified
> sources, whether
>
> it’s detailed data like CSV records, stored information in systems
> such as ChromaDB,
>
> or live updates from oficial websites. This method ensures responses
> are based on
>
> actual data, eliminating guesswork and maintaining full transparency.
> By accessing
>
> the internet in real time via DuckDuckGo, the system retrieves the
> most current details
>
> on laws, country policies, and alerts something static large language
> models cannot do.
>
> This feature is especially helpful in areas where tax rules frequently
> change.
>
> • Live Data Access: Since all data sources wether originated from
> uploaded CSVs,
>
> government websites, or ChromaDB documents are trackable, users can
> trust the in-
>
> formation and it supports audits and compliance efforts.
>
> • Multi-Format Data Integration: For more detailed comparisons, like
> evaluating
>
> excise taxes across nations or matching tariffs with trade deals, the
> system smoothly
>
> integrates various formats including structured (CSV), semi-structured
> (PDFs, forms),
>
> and unstructured web content.
>
> • Ofline Functionality: Also, connection to Dnext Data, a carefully
> curated tax
>
> database, enables hybrid retrieval methods that function reliably even
> without internet
>
> access, ensuring accuracy and consistency regardless of the situation.
>
> 17

Chapter 2. State of Technology and Project Pipeline

2.4 Data Memory : Semantic Search with FAISS and

> ChromaDB

Traditionally, assessing trends in taxation or reviewing changes in
policy over time often

requires consulting static documents or external records. This process
is greatly improved

through using a two layered memory system that understands the context
of the data.

> • FAISS(Facebook AI Similarity Search) \[6\]:enables swift, in memory
> comparison
>
> of vectors for documents and CSV data uploaded during the current
> session. This
>
> allows the system to analyze information quickly based on what the
> user is actively
>
> working on.
>
> • ChromaDB: acts as a long term storage solution, saving processed and
> vectorized
>
> documents from previous interactions. This setup allows the system to
> access relevant
>
> past data, making it possible to recognize patterns over extended
> periods, respond
>
> intelligently in ongoing conversations, and pick up where it left off
> even after weeks.

Combining these two methods creates a system capable of consistent,
flexible, and context-

aware assistance across multiple sessions, supporting a smooth flow of
information and his-

tory retention.

> TAXI’s sophisticated memory system allows it to analyze current and
> historical regula-

tions, monitor how rules evolve across different regions, and maintain a
continuous database

of knowledge for easy access and reference.

2.5 Embeddings and the Transformer: Key Components

> of Language Understanding

Embeddings are a method used by AI systems to understand, compare, and
retain informa-

tion. They work by converting text such as prompts, documents, or comma
separated data

into complex numerical vectors that capture the underlying meaning of
words. This format

allows the AI to analyze and distinguish between different types of
language, formats, and

specialized content effectively.

> 18

Chapter 2. State of Technology and Project Pipeline

> Embedding representations form a fundamental component of the
> Transformer based

architecture \[7\] that powers this advanced AI technology. Similar to
the core Transformer

design, individual words or segments are converted into numerical
vectors and processed

through multiple layers of self attention, enabling the model to grasp
how words relate

to each other in context. To preserve word order, positional encoding is
applied, which

is essential when analyzing legal statements, numerical figures, or
jurisdiction-specific tax

rules. The Transformer subsequently generates or ranks responses based
on its processed

knowledge.

> TAXI employs two primary types of embeddings: first, Hugging Face’s
> adaptable embed-

dings, which excel at rapidly identifying similarities across large
document collections ideal

for searching extensive datasets. Second, Sentence Transformers, which
are more suited for

domain specific tasks such as interpreting multilingual legal texts or
analyzing complex fi-

nancial documents. These embeddings are particularly valuable in fields
like law and finance,

where precision and careful wording are critical. The resulting vectors
are then integrated

with vector databases such as FAISS or ChromaDB to enable fast, real
time retrieval of

relevant information.

2.5.1 Embedding Models

> • Hugging Face Embeddings \[8\]: Optimized for large-scale document
> similarity and
>
> rapid search across extensive datasets.
>
> • SentenceTransformers: Tailored for multilingual legal and financial
> content, en-
>
> abling precise understanding of complex jurisdictional language.
>
> 19

Chapter 2. State of Technology and Project
Pipeline<img src="./ngdyzh2p.png"
style="width:5.52187in;height:3.40516in" />

> Figure 2.3: Transformer Language Understanding in TAXI
>
> \[9\]

2.6 Optimization Infrastructure: DeepSpeed, Ollama, and

> LangChain

2.6.1 DeepSpeed

Microsoft’s DeepSpeed \[10\] library enables highly eficient model
training and inference, min-

imizing GPU memory consumption and inference latency. This allows TAXI’s
large models

to operate on commercially accessible hardware while maintaining real
time performance.

2.6.2 Ollama

Ollama \[11\] offers local deployment for full privacy and regulatory
compliance. Sensitive

fiscal data is processed entirely within enterprise servers, eliminating
dependency on external

clouds and ensuring ofline capabilities for secure institutions.

> 20

Chapter 2. State of Technology and Project Pipeline

2.6.3 LangChain

LangChain \[12\] acts as the orchestration layer, managing input
parsing, document chunking,

embedding generation, retrieval coordination across FAISS, ChromaDB, and
web searches,

and final output generation. This orchestration allows TAXI to perform
complex multi step

reasoning autonomously.

2.7 Core Technologies and Functional Roles

> Table 2.1: Core Technologies and Functional Roles in TAXI

||
||
||
||
||
||
||
||
||
||
||
||
||

> 21

Chapter 2. State of Technology and Project
Pipeline<img src="./lxsd2cnh.png"
style="width:1.57483in;height:0.82886in" />

Project Pipeline:implementation and evaluation

This section provides an in-depth explanation of the foundational data
system underlying

the TAXI platform. It combines intelligent AI reasoning with business
analytics to gather

and interpret trade and tariff information worldwide. Managing trade
data from numerous

countries involves integrating various sources, continuously updating
information, and align-

ing different data formats. The data pipeline is designed to reliably
collect, verify, enhance,

and prepare data for use. This ensures that both AI features and
decision-making tools

receive accurate, validated data inputs, supporting effective trade
analysis and insights.

2.8 Data Collection

2.8.1 International Trade Centre (ITC) API

The International Trade Centre’s API is an essential tool for accessing
comprehensive cus-

toms data. Users can examine specific details such as tariff rates
assigned at the precise

eight-digit level of the Harmonized System (HS), and various types of
duties including Most

Favored Nation (MFN), preferential, and bilateral tariffs. It also
provides information on

commitments related to WTO-bound rates.

> Figure 2.4: International Trade Centre (ITC) Logo
>
> \[13\]
>
> Furthermore, the API supplies data on import quotas and market
> specific trade pref-

erences that differ between nations. When integrated with the TAXI
platform, this system

helps users analyze how tariffs fluctuate across more than 40 different
agricultural prod-

ucts traded internationally. This allows for the identification of
country specific duty rates,

special trade agreements, regional free trade zones, and seasonal tariff
adjustments.

> 22

Chapter 2. State of Technology and Project
Pipeline<img src="./vl5uhxe3.png"
style="width:1.57468in;height:0.92267in" />

2.8.2 FedEx API and Dnext Premium Data

The FedEx API for Freight and Routing provides essential logistical
insights. It supplies

information such as routing schedules from origin to destination, up to
date shipping rates,

historical delivery times, and patterns of seasonal freight
fluctuations. These details en-

able smooth integration of real time CNF (Cost plus Freight) pricing
models directly into

dashboard modules.

> Figure 2.5: FedEx Logo
>
> \[14\]
>
> Additionally, Dnext Premium Data enhances the platform by offering
> historical market

price trends, forward looking flat price models (estimations of future
price curves), and

advanced premium pricing scenarios that account for risk factors, supply
disruptions, and

macroeconomic changes. This comprehensive data supports energetic future
price simula-

tions within the dashboard environment.

> 23

Chapter 2. State of Technology and Project
Pipeline<img src="./d3fyhhza.png"
style="width:4.87198in;height:4.42681in" />

> Figure 2.6: FedEx Data Retrieval and Integration Workflow in TAXI
> Platform

2.8.3 Automated Web Scraping and Pipeline Orchestration

When oficial APIs or large datasets are not directly available,
automated web scraping

becomes essential for gathering regulatory, tariff, and logistics data
from various governmen-

tal and institutional sources. Web scrapers systematically crawl these
portals, capturing

unstructured data and transforming it into clean, machine-readable JSON
or CSV formats.

> The entire data ingestion pipeline is orchestrated using Dagster, a
> highly modular or-

chestration framework capable of managing complex ETL operations.
Dagster schedules

and monitors the complete extraction and transformation processes from
diverse sources,

including:

> • ITC API (International Trade Centre)
>
> • FedEx API (logistics and freight routing data)
>
> • Dnext Premium Data (forward price models, macro indicators)
>
> 24

Chapter 2. State of Technology and Project
Pipeline<img src="./05zl0vhg.png"
style="width:1.29917in;height:0.91135in" /><img src="./2pohjx4a.png"
style="width:5.19689in;height:2.10472in" />

> • Web scraped portals (for regulatory updates)
>
> Figure 2.7: Dagster Logo
>
> \[15\]
>
> Once ingested, the data flows through a validation and normalization
> layer:
>
> • Schema validation and integrity checks.
>
> • Removal of duplicates and missing records.
>
> • Conversion to unified formats (currency, units, timestamps).
>
> • Enrichment with additional metrics for CNF pricing models and risk
> forecasting.
>
> The processed data is then securely stored into Snowflake and local
> storage layers for

subsequent use by both the Agentic AI system and analytical dashboards.

> Figure 2.8: Dagster Assets Orchestration
>
> 25

Chapter 2. State of Technology and Project
Pipeline<img src="./u0p1g3sr.png"
style="width:5.19681in;height:2.75799in" /><img src="./yywgv4cx.png"
style="width:2.59835in;height:1.09316in" />

> Figure 2.9: Dagster Job Extraction Pipelines
>
> Thanks to Dagster’s modular design, the entire pipeline remains fully
> transparent, au-

ditable, and resilient. Any pipeline failure can be traced, monitored,
and resolved with

precision, ensuring consistent data availability for downstream
applications such as AI rea-

soning and interactive analytics.

2.8.4 Centralized Data Storage in Snowflake

All verified data is loaded into Snowflake, a cloud based data warehouse
serving as the

central core for the entire TAXI system. This single database supports
multiple data types,

such as tariff tables segmented by country, historical product pricing
records, intercountry

tariff mappings, and tables for freight, CNF, FLAT, and premium
agreements.

> Figure 2.10: Snowflake Logo
>
> \[16\]
>
> Thanks to Snowflake’s built in SQL functions, users can conduct swift
> data queries,

easily extract important features, and smoothly connect with other
tools. Notably, it links

> 26

Chapter 2. State of Technology and Project
Pipeline<img src="./smroywut.png"
style="width:5.84638in;height:1.80404in" />

seamlessly with the Agentic AI platform for semantic search capabilities
and integrates

effortlessly with Power BI for operational analysis and real time
dashboarding.

> Essentially, Snowflake is the most dependable and unified source of
> information for all

parts of the TAXI platform.

> Figure 2.11: Logical Data Structure of Snowflake within TAXI Pipeline

2.8.5 Feature Engineering and Unified Data Preparation

The process of preparing data for decision support involves transforming
raw information into

meaningful features. For tax related analysis, key inputs include
historical duty amounts,

preferential trade agreements, most-favored-nation (MFN) tariffs, and
quota-based duty lim-

its.

> When it comes to pricing, features such as CNF pricing (cost and
> freight), comprehen-

sive FLAT pricing (including forward premiums) and volatility scores
derived from forward

contract fluctuations are used. These features serve as essential
indicators of trade stability

and evolving market conditions.

> They are fundamental for both:
>
> • AI systems that reason through complex tax regulations.
>
> • Business dashboards that assist with pricing, profit evaluations,
> and sourcing decisions.
>
> The structured data pipeline supplies two major end-users:
>
> • Agentic AI Reasoning System: A dedicated AI framework focused
> exclusively on
>
> tariff and tax rule reasoning. It integrates:
>
> – FAISS for semantic similarity search.
>
> 27

Chapter 2. State of Technology and Project Pipeline

> – ChromaDB for long-term vector memory management.
>
> – DeepSeek-R1 for multilingual reasoning and tax logic generation.
>
> – LangChain for orchestration of embedding pipelines, retrieval, and
> agent work-
>
> flow control.
>
> – Retrieval-Augmented Generation (RAG) for dynamic context injection
> and
>
> real-time query interpretation.
>
> • Business Intelligence Dashboard: A comprehensive Power BI interface
> that inte-
>
> grates both tax and pricing datasets, enabling:
>
> – Real-time profit margin analysis.
>
> – CNF, FLAT, and premium pricing comparisons.
>
> – Interactive filtering across products, years, trading partners, and
> contract struc-
>
> tures.
>
> This architecture maintains strict separation between AI and BI
> workflows, ensuring

that TAXI can simultaneously meet compliance needs while delivering
actionable financial

insights.

> In summary, this section has described the comprehensive data
> preparation system pow-

ering the TAXI platform. Its fully automated infrastructure consolidates
regulatory, pricing,

and logistical information into a unified, scalable repository enabling
both intelligent AI rea-

soning and real time operational reporting. Its modular design ensures
future adaptability

for new commodities, trade partners, and evolving legal frameworks.

Conclusion

This chapter provides a comprehensive explanation of the smart AI system
architecture

and the sophisticated data pipeline that drives the TAXI platform. It
begins by examining

the current regulatory and business environments, then details how the
platform integrates

diverse data sources—like tariff schedules, logistics data, and pricing
strategies through

fully automated workflows managed by Dagster and stored centrally in
Snowflake. This

architecture ensures real-time data access, uniformity, and the ability
to scale eficiently

> 28

Chapter 2. State of Technology and Project Pipeline

for both AI operations and business insights. Central to TAXI’s
intelligent reasoning is a

state of the art Transformer based framework that employs embedding
models to interpret

detailed financial, legal, and multilingual datasets at a deep level.
Technologies such as

DeepSeek-R1, FAISS, ChromaDB, LangChain, DeepSpeed, and Ollama
collaborate to as-

sist adaptable, modular reasoning processes, enable live data sourcing
analysis, and produce

decisions that are fully auditable. Thanks to this well organized
system, TAXI goes be-

yond simple question-answering,it performs advanced, context aware
reasoning that adapts

to the constantly developing environment of international tax rules. By
the culmination

of this development phase, the platform delivers a strong,
production-ready infrastructure

capable of powering real-time dashboards, supporting scalable AI logic,
and deploying solu-

tions smoothly to address practical needs in global trade, tax
assessments, and procurement

optimization.

> 29
>
> 3 Agentic AI Modeling and Implementation

Introduction

This section outlines the development and testing process of the TAXI
Agentic AI system.

After assembling and preparing the data carefully, the focus shifted
toward managing so-

phisticated language models, processing local data workflows, performing
semantic searches

with vector representations, integrating reasoning components, and
creating user-friendly in-

terfaces. The TAXI platform blends state of the art retrieval-augmented
generation (RAG)

methods with fully local AI operations to provide personalized tariff
insights, all while safe-

guarding user privacy and maintaining clarity.

The chapter offers a detailed look at the system’s architecture,
essential models, orchestra-

tion approaches, and evaluation techniques, providing a thorough
overview. Finally, the

TAXI pipeline proves that it is feasible to develop a dependable,
AI-driven decision sup-

port system that operates on private infrastructure, delivers quick
responses, and eficiently

combines data from multiple sources.

> 30

Chapter 3. Agentic AI Modeling and Implementation

3.1 Working Environment

3.1.1 Hardware Setup

For development and testing purposes related to TAXI, a high performance
workstation

was utilized with the following specifications:

> • Device: Lenovo LOQ Gaming Laptop
>
> • Processor: Intel® CoreTM i5-12450HX (8 cores, up to 4.40 GHz Turbo
> Boost)
>
> • Memory: 32 GB DDR5 RAM (4800 MT/s)
>
> • Graphics Card: NVIDIA® GeForce RTXTM 3050 with 6 GB GDDR6 dedicated
>
> memory
>
> • Storage: 512 GB NVMe SSD
>
> • Display: 15.6-inch Full HD IPS screen with 144Hz refresh rate
>
> • Operating System: Windows 11 x64 (custom installation)

3.1.2 Software Setup

The TAXI platform was fully developed using a robust and modular
software stack designed

to handle data ingestion, processing, AI reasoning, and visualization.
The following tools

and frameworks were employed:

> • Programming Language: Python (leveraging advanced typing, f-strings,
> and com-
>
> patibility with AI frameworks).
>
> • Development Tools:
>
> – Visual Studio Code (primary development environment).
>
> • Environment Management: Ubunto and venv for isolated virtual
> environments.
>
> • ETL Orchestration: Dagster for scheduling and orchestrating data
> pipelines.
>
> • Data Storage and Querying:
>
> 31

Chapter 3. Agentic AI Modeling and Implementation

> – Apache Parquet for eficient columnar data storage.
>
> – DuckDB for fast, in memory SQL based querying.
>
> • Data Manipulation: pandas for data processing and feature
> generation.
>
> • Embedding Models:
> SentenceTransformers(all-mpnet-base-v2)forhigh-dimensional
>
> text embeddings.
>
> • Semantic Search: FAISS for approximate nearest neighbor vector
> retrieval.
>
> • AI Orchestration: LangChain for retrieval-augmented generation (RAG)
> orchestra-
>
> tion.
>
> • Vector Storage: ChromaDB for persistent storage of semantic
> embeddings.
>
> • Local LLM Inference:
>
> – Ollama for on-device language model hosting.
>
> – DeepSeek R1 as the core transformer based reasoning model.
>
> • Web Search Integration: duckduckgo_search for live online context
> enrichment.
>
> • User Interface: Gradio for web based interactive interface.
>
> 32

Chapter 3. Agentic AI Modeling and Implementation

> Table 3.1: Software Components and Their Functional Roles in the TAXI
> Platform

||
||
||
||
||
||
||
||
||
||
||
||
||
||
||
||
||
||

> 33

Chapter 3. Agentic AI Modeling and
Implementation<img src="./oshvbab3.png"
style="width:1.57483in;height:1.04798in" />

3.2 Models and Techniques

3.2.1 DeepSeek R1

DeepSeek R1\[17\] is the primary AI component powering the TAXI
analytical platform. This

multilingual advanced language model is tailored specifically for
handling structured regu-

latory data with high eficiency. Deployed locally through Ollama,
DeepSeek R1 guarantees

user privacy, fast response times, and functions independently of
external cloud services.

> Figure 3.1: DeepSeek R1 Logo
>
> Main features:
>
> • Designed for strong logical reasoning, proficient in interpreting
> tables, and capable of
>
> following complex instructions.
>
> • Supports processing of extensive contextual information (up to
> 32,768 tokens) by syn-
>
> thesizing data from multiple sources.
>
> • Quantized for optimized GPU performance, eliminating reliance on
> external APIs.
>
> • Functions as the main reasoning engine after extracting pertinent
> data from FAISS
>
> and ChromaDB.

3.2.2 FAISS

Developed by Facebook AI, FAISS\[18\] is essential for TAXI’s semantic
search functionalities.

It converts datasets into 768-dimensional dense vectors, enabling rapid
similarity compar-

isons.

> 34

Chapter 3. Agentic AI Modeling and
Implementation<img src="./jecvadgl.png"
style="width:1.57476in;height:0.8858in" /><img src="./4xcswo3z.png"
style="width:4.54716in;height:2.52465in" />

> Figure 3.2: FAISS Logo
>
> Key capabilities:
>
> • Fast retrieval of related records from millions of entries.
>
> • High-accuracy searches using IndexFlatL2 for precise vector
> matching.
>
> • Approximate nearest neighbor algorithms for fast assembly of
> relevant context.
>
> • On the fly creation of mini FAISS indices during queries to enhance
> RetrievalQA
>
> performance.

RetrievalQA stands as a powerful tool in overcoming one of the
significant challenges of

LLM-based systems the limitation of providing answers based solely on
learned information

up to the training point. This tool serves as a collaborative solution,
enabling the extraction

of novel information not covered during the model’s training.

In the realm of RetrievalQA, passing a retriever such as VectorStore or
custom datasets

provides a means to query pertinent data or documents. This, in turn,
empowers the LLM

to generate responses based on a broader and more up-to-date
understanding of the context.

> Figure 3.3: RetrievalQA Architecture Overview
>
> 35

Chapter 3. Agentic AI Modeling and
Implementation<img src="./y0p5ytax.png"
style="width:1.5748in;height:1.10471in" />

> A notable advantage of RetrievalQA lies in its ability to shed light
> on the origins of LLM’s

responses. By indicating the sources from which answers are derived, it
becomes possible

to assess the credibility of the model’s responses and delve into the
underlying information

that forms the basis of each answer. \[19\]

> This architecture allows TAXI to eficiently locate highly relevant
> past tariff data across

more than 40 agricultural commodities and multiple trade flows.

3.2.3 ChromaDB

While FAISS operates in volatile memory for real-time performance,
ChromaDB provides

persistent storage of vectorized data, ensuring long-term durability.

> Figure 3.4: ChromaDB Logo
>
> \[20\]
>
> ChromaDB enables:
>
> • Secure storage of historical tax records and previously indexed
> datasets.
>
> • Semantic searches across historical sessions stored in persistent
> databases.
>
> • Seamless integration with LangChain’s vector storage modules.
>
> ThehybridcombinationofFAISSforrecentqueriesandChromaDBforlong-termarchives

grants TAXI adaptive and consistent recall capabilities, critical for
longitudinal tariff anal-

ysis.

3.2.4 LangChain

The reasoning and data orchestration processes in TAXI are governed by
LangChain a spe-

cialized framework for combining language models with external
structured data sources.

> 36

Chapter 3. Agentic AI Modeling and
Implementation<img src="./41wa5d33.png"
style="width:1.57483in;height:0.88191in" /><img src="./wgiej1gp.png"
style="width:1.96862in;height:1.96862in" />

> Figure 3.5: LangChain Logo
>
> LangChain coordinates:
>
> • Query orchestration across FAISS, ChromaDB, and live web search.
>
> • Construction of complex prompt chains that incorporate structured
> context.
>
> • Aggregation of multiple retrieved data segments into coherent input
> prompts.
>
> • Management of the RetrievalQA process within RAG pipelines.
>
> LangChain simplifies the overall integration of structured and
> unstructured data streams

into a single unified reasoning pipeline.

3.2.5 DuckDuckGo (Web Retrieval)

Although not directly responsible for tariff database access, DuckDuckGo
search serves as

an optional live search module for augmenting TAXI’s knowledge with
external updates.

> Figure 3.6: DuckDuckGo Logo
>
> \[21\]
>
> Web search covers:
>
> • Updates on government fiscal policies.
>
> 37

Chapter 3. Agentic AI Modeling and
Implementation<img src="./1yc5ddh5.png"
style="width:1.57476in;height:1.57476in" />

> • Latest revisions to trade agreements.
>
> • International trade disputes and sanctions.
>
> • New regulatory notices not yet integrated into oficial datasets.
>
> The lightweight duckduckgo_search Python package is used to retrieve
> up to six rele-

vant search snippets. These are then injected into the prompt structure
through LangChain

for enhanced web-aware responses.

3.2.6 DeepSeed (Agent Control Layer)

Positioned above the core model stack, DeepSeed serves as the
intelligent agent controller

that governs tool selection and reasoning pathways within TAXI.

> Figure 3.7: DeepSeed Logo
>
> \[22\]
>
> DeepSeed responsibilities:
>
> • Directs the invocation of FAISS, ChromaDB, live web search, and
> reasoning models.
>
> • Manages iterative and self-correcting multi-step reasoning tasks.
>
> • Integrates factual data retrieval with natural language generation.
>
> • Decides dynamically whether to operate over local structured data or
> retrieve external
>
> web context.
>
> Through DeepSeed, TAXI transcends traditional chatbot boundaries and
> operates as a

fully autonomous, agentic AI system capable of real-time global trade
analysis.

> 38

Chapter 3. Agentic AI Modeling and Implementation

3.3 Modeling and Development Approach

The TAXI Agentic AI system adopts a fundamentally different approach
compared to tra-

ditional supervised fine-tuning by employing a versatile, hybrid
architecture that integrates

multiple processing techniques. Its design merges retrieval-based
reasoning with real-time

semantic search, allowing rapid adaptation to new information without
requiring lengthy

retraining cycles.

> At the core of the system, several key principles govern its
> operation:
>
> • Embedding-Based Filtering: Relevant data entries are selected
> through semantic
>
> similarity using embedding-based filters, ensuring that only the most
> pertinent context
>
> is included in each prompt.
>
> • Multi-Document Reasoning: The DeepSeek R1 model processes multiple
> re-
>
> trieved documents simultaneously, synthesizing them into logically
> consistent and con-
>
> cise answers.
>
> • Separation of Functional Layers: The architecture distinctly
> separates data stor-
>
> age, retrieval, and reasoning components, promoting scalability and
> modular extensi-
>
> bility.
>
> When users upload new datasets in formats such as CSV or JSONL through
> the Gradio

interface, the following data ingestion pipeline is triggered:

> • File Conversion: Uploaded files are instantly converted into Parquet
> format using
>
> PyArrow, enabling highly eficient columnar storage.
>
> • Table Unification: The resulting Parquet files are registered into
> DuckDB, which
>
> performs high-performance SQL operations to merge multiple datasets
> into a unified
>
> analytical table.
>
> • Row Flattening: Each row of the unified table is transformed into a
> flattened, string-
>
> based representation by concatenating all column values. This format
> is optimized for
>
> embedding generation.
>
> • Semantic Embedding: Theflattenedrowsarepassedthroughthe
> Sentence-Transformers
>
> model (all-mpnet-base-v2), producing 768-dimensional dense vector
> embeddings.
>
> 39

Chapter 3. Agentic AI Modeling and Implementation

> • Vector Indexing: Theseembeddingsarestoredinaglobal
> FAISSindex(IndexFlatL2),
>
> which serves as a rapid access short-term memory bank capable of
> eficiently retrieving
>
> semantically similar records even across millions of entries.
>
> • Long-Term Persistence: In parallel, historical datasets and previous
> interactions
>
> are securely stored within ChromaDB, providing persistent long-term
> memory that
>
> supports historical recall and contextual continuity across sessions.

3.4 Live Query Flow and Reasoning Pipeline

The TAXI platform processes user queries through a highly modular,
multi-stage reasoning

pipeline that ensures both accuracy and adaptability. The overall flow
can be broken down

into the following structured stages:

3.4.1 User Query Submission

The process begins when a user inputs a natural language question
through the Gradio web

interface. This interface provides:

> • An interactive chat window for submitting questions.
>
> • File upload modules for dataset ingestion.
>
> • Live toggles for enabling or disabling web-based search
> augmentation.

3.4.2 Semantic Embedding Generation

Upon receiving the user input:

> • The natural language query is transformed into a 768-dimensional
> dense vector using
>
> the Sentence-Transformers model (all-mpnet-base-v2).

3.4.3 Vector Similarity Search (FAISS)

The generated embedding is passed to FAISS, which performs:

> • A high-speed similarity search across the indexed knowledge base.
>
> 40

Chapter 3. Agentic AI Modeling and
Implementation<img src="./3fyqh0i2.png"
style="width:5.52164in;height:3.26549in" />

> • Retrieval of the top-k semantically closest row representations.
>
> • Creation of an initial, highly relevant data context for the query.
>
> Figure 3.8: FAISS-based Vector Similarity Workflow in TAXI Platform
>
> \[23\]

3.4.4 Optional Web Augmentation (DuckDuckGo)

If web search is activated:

> • DuckDuckGo retrieves up to six live snippets related to the query.
>
> • Web snippets may include recent policy changes, real-time market
> updates, or newly
>
> published legal documents not yet present in local storage.
>
> • These snippets are passed forward for inclusion in the final prompt
> assembly.

3.4.5 Prompt Assembly (LangChain)

Using LangChain, the system orchestrates:

> • Combination of FAISS-derived row strings with any web snippets.
>
> 41

Chapter 3. Agentic AI Modeling and
Implementation<img src="./ulb1gwwt.png"
style="width:5.52181in;height:3.48426in" />

> • Structuring of the full prompt into a Retrieval-Augmented Generation
> (RAG) template
>
> compatible with RetrievalQA.
>
> • Construction of multi-source contextual input for downstream
> reasoning.
>
> Figure 3.9: LangChain Prompt Orchestration and Retrieval Pipeline in
> TAXI Platform
>
> \[24\]

3.4.6 Reasoning and Response Generation (DeepSeek R1 via Ol-

> lama)

The fully assembled prompt is forwarded to DeepSeek R1, operating
locally through Ol-

lama. This stage involves:

> • Complex multi-document reasoning across embedded data and real-time
> information.
>
> • Dynamic fusion of structured tabular content with unstructured web
> data.
>
> • Fallback extraction techniques, such as regex parsing, for
> validating numerical outputs
>
> if confidence scores are low.
>
> 42

Chapter 3. Agentic AI Modeling and Implementation

3.4.7 Answer Presentation and Debugging Transparency

The generated answer is displayed directly in the Gradio interface.
Additional debug fea-

tures include:

> • FAISS similarity scores for retrieved documents.
>
> • The full source row strings contributing to the response.
>
> • Confidence scores and extracted numerical validations.
>
> • Full prompt context for model interpretability and auditing.

3.4.8 Dataset Ingestion and Index Update

New datasets are seamlessly integrated into the system via:

> • File upload in CSV format via Gradio.
>
> • Conversion to columnar Parquet format using PyArrow.
>
> • Unified merging within DuckDB for optimized querying.
>
> • Row flattening and embedding with Sentence-Transformers.
>
> • Real-time update of the FAISS global index, incorporating new
> embeddings into the
>
> searchable knowledge base.

3.5 Validation and Interactive Deployment

The TAXI Agentic AI platform features an intuitive, easy-to-navigate
interface built with

Gradio, serving simultaneously as a control dashboard for administrators
and an interactive

demo for end users. Users can effortlessly manage data uploads,
retrieval tasks, and access

real-time reasoning functions.

> Uploading new datasets in CSV or JSONL formats is straightforward
> through a dedicated

file upload section. After upload, the system automatically converts the
data into Parquet

format using PyArrow and reconstructs the FAISS index instantly. This
means new data

becomes immediately searchable without requiring manual intervention.

> 43

Chapter 3. Agentic AI Modeling and Implementation

> An optional toggle allows users to activate or deactivate live web
> searches via Duck-

DuckGo. When enabled, the system fetches current online information,
enhancing local

data with fresh insights—particularly useful for tracking recent
developments in trade poli-

cies, tariffs, or international treaties.

> For users seeking detailed explanations of decision-making processes,
> debug mode re-

veals all internal workings, including:

> • FAISS similarity scores
>
> • Source documents retrieved during searches
>
> • Vector distances
>
> • Prompts used in reasoning

This promotes full transparency for troubleshooting and validation.

> The system includes an interactive query input where questions in
> natural language

are processed in real-time. The AI searches across multiple data sources
to generate precise,

comprehensive answers.

> At its core, the TAXI architecture is designed for continual learning
> and fast updates,

avoiding lengthy retraining periods. When datasets are added, they
instantly enhance the

AI’s knowledge base via FAISS, granting immediate access to new
information.

> Upon receiving a question, the system:
>
> • Converts the query into a 768-dimensional vector using
> Sentence-Transformers.
>
> • FAISS performs a semantic search to identify the most relevant
> records based on this
>
> vector.
>
> • If web search is activated, DuckDuckGo retrieves up to six real-time
> snippets to
>
> enrich the internal data.
>
> • LangChain compiles both FAISS and web snippets into a comprehensive
> Retrieval-
>
> Augmented Generation (RAG) prompt.
>
> • The final prompt is passed to DeepSeek-R1, which synthesizes
> multi-source data into
>
> a precise answer.
>
> 44

Chapter 3. Agentic AI Modeling and Implementation

> • When numerical confidence is low, fallback techniques such as regex
> extraction are
>
> applied to ensure answer accuracy.
>
> Thefinal responseis displayed withinthe Gradiochatwindow. Ifdebug
> modeisactive, all

intermediate steps, data sources, and full reasoning traces are
presented, providing complete

visibility for development, auditing, and troubleshooting.

3.6 Model Evaluation

Before demonstrating real-world examples, this section presents the
evaluation results of the

TAXI Agentic AI system. The assessment covers both the end-to-end
retrieval pipeline

and the internal memory subsystem.

3.6.1 Retrieval Pipeline Evaluation

The retrieval pipeline integrates multiple live data sources and
reasoning agents. The fol-

lowing table summarizes the overall performance across the key
components:

> Table 3.2: Retrieval Pipeline Evaluation Metrics

||
||
||
||
||
||
||

> These results confirm TAXI’s strong capabilities in dynamic regulatory
> reasoning, cross-

format data retrieval, and real-time adaptability.

> 45

Chapter 3. Agentic AI Modeling and Implementation

3.6.2 Semantic Memory Evaluation

The memory system supports both short-term semantic retrieval and
long-term regulatory

knowledge accumulation. Its performance is assessed using the following
metrics:

> • Vector Matching Accuracy: Ability to correctly identify semantically
> relevant doc-
>
> uments.
>
> • Temporal Consistency: Ability to preserve continuity across
> sessions.
>
> • Cross-Format Retrieval: Ability to retrieve information across
> formats (CSV, PDF,
>
> legal texts, web).
>
> The detailed evaluation of the memory components is provided below:
>
> Table 3.3: Semantic Memory Components Evaluation

||
||
||
||
||

> These evaluations demonstrate TAXI’s dual capacity for both immediate
> responsiveness

and robust long-term regulatory knowledge management.

3.6.3 Practical Demonstrations and Actual Behavior of the Agent

This section displays real world examples that emphasize how the TAXI
Agentic AI system

functions in various user scenarios. These demonstrations highlight its
hybrid approach,

integrating multiple data sources, local embeddings, real-time web
searches, and structured

reasoning.

3.6.3.1 Example 1 — Price Data Analysis from CSV Uploads

As shown in Figure 3.10, after a user uploads pricing data, they ask:

> 46

Chapter 3. Agentic AI Modeling and
Implementation<img src="./3nsy4rk3.png"
style="width:5.84635in;height:2.56825in" />

> • “Analyse this file in terms of prices, which is the high priced
> product? as well provide
>
> me with the structure of this file .”
>
> The model automatically analyzes the columns, identifies date ranges,
> parses numerical

fields, and deduces product prices directly from the data. This
demonstrates its versatility

in interpreting general datasets, not just tax-related information.

> Figure 3.10: Price Structure and Product Analysis from CSV Upload

3.6.3.2 Example 2 — Numerical Analysis of Tax Rates

As illustrated in Figures 3.11 and 3.12, the agent can handle complex
questions like:

> • “What is the highest and lowest tax rate, and what type of tax are
> they?”
>
> • “What are the maximum and minimum tax rates for duty categories?”
>
> The system uses FAISS to find relevant data, then extracts numeric
> information and

applies internal parsing and mathematical reasoning to determine exact
maximum and min-

imum rates. This demonstrates the agent’s strong ability to interpret
tabular data powered

by DeepSeek R1.

> 47

Chapter 3. Agentic AI Modeling and
Implementation<img src="./af4q04rg.png"
style="width:5.84635in;height:2.67793in" /><img src="./zs1wrf0x.png"
style="width:5.84635in;height:2.61395in" />

> Figure 3.11: Tax Reasoning Example 1
>
> Figure 3.12: Tax Reasoning Example 2

3.6.3.3 Example 3 — Country-Specific Tax Inquiry

In Figure 3.13, a user requests:

> • “What is the duty rate the USA applies to imports from Armenia?”
>
> Theagentcorrectlydetectsdutypercentages,
> verifiesthemwithcontextualdata, manages

ambiguous entries, and transparently reports its confidence levels. Even
when conflicting

data appears, the system reasons step-by-step to produce a probabilistic
conclusion.

> 48

Chapter 3. Agentic AI Modeling and
Implementation<img src="./oocuteq0.png"
style="width:5.84634in;height:2.67415in" /><img src="./1nnxuedh.png"
style="width:5.84647in;height:2.267in" />

> Figure 3.13: Duty Rate Reasoning for Armenia-USA Trade

3.6.3.4 Example 4 — Integration with Live Web Searches

When web search mode is activated (see Figure 3.14), the agent enhances
its answers by

retrieving real-time information from DuckDuckGo. For example:

> • “Does Colombia impose a zero tax rate on all countries?”
>
> The agent finds details about Colombia’s tax treaties and incorporates
> external legal

information that is not stored locally. This demonstrates TAXI’s ability
to blend local data

with live internet content, providing more accurate and current
responses through Retrieval-

Augmented Generation (RAG) chains.

> Figure 3.14: Web Retrieval Reasoning Example
>
> 49

Chapter 3. Agentic AI Modeling and
Implementation<img src="./uraqmktm.png"
style="width:1.62347in;height:0.9132in" />

3.6.3.5 Summary

Through these examples, the TAXI Agentic AI system displays:

> • End-to-end automation from CSV uploads to immediate semantic search
> capabilities.
>
> • Advanced reasoning over multi-dimensional tables involving complex
> calculations.
>
> • Flexibility to adapt to new data without needing retraining.
>
> • Use of real-time web data to improve understanding and accuracy.
>
> • Transparent processes displayed via debug logs, data contexts, and
> reasoning pathways
>
> within Gradio interface.

3.7 Interactive Analytics and Visual Data Exploration

In addition to the AI-powered Agentic system, TAXI provides a
comprehensive, user-

friendly interactive analytics dashboard ,designed with Microsoft Power
BI, it makes complex

information easy to understand through powerful visual tools. The
dashboard combines de-

tailed tables, charts, and interactive elements, giving users clear
insight into tax schemes

and pricing details.

> This dashboard enables professionals, policymakers, and researchers to
> visually explore

processed tariff and price data. The dashboard is organized into
multiple modules, each dedi-

cated to a specific aspect of trade analysis and cost evaluation. By
combining detailed tables,

graphical representations, and interactive features, the dashboard
offers an unprecedented

level of transparency and actionable insight for decision-makers in
international trade.

> Figure 3.15: Power BI Logo
>
> \[25\]
>
> 50

Chapter 3. Agentic AI Modeling and
Implementation<img src="./semyqwgc.png"
style="width:5.84647in;height:3.0445in" />

3.7.0.1 Tariff Overview Module

The Tariff Overview section (see Figure 3.16) allows users to
investigate applied tariffs

between different partner countries and across various agricultural
products. It presents

both MFN (Most Favored Nation) duties and non-MFN preferential rates in
a structured

matrix format, where rows correspond to partner countries and columns
represent specific

commodities such as corn, soybeans, wheat, barley, and others. This
configuration supports

side by side cross country comparisons, revealing tariff differentials
that may affect sourcing,

pricing, and strategic trade decisions.

> Figure 3.16: Interactive Tariff Overview Table Showing Applied Duties
> Across Countries and Products.

3.7.0.2 Product-Level Tax Analysis

In the Product Tax Module (see Figure 3.17), users can monitor how
tariff rates evolve across

time for individual products. This trend visualization allows experts to
observe fluctuations

in applied duties, supporting predictive analysis of trade costs and
policy shifts.

> 51

Chapter 3. Agentic AI Modeling and
Implementation<img src="./zo4ujjod.png"
style="width:5.84651in;height:3.08651in" /><img src="./oeqihukx.png"
style="width:5.84664in;height:2.99213in" />

> Figure 3.17: Product Taxation Trends Over Time for Key Commodities.

3.7.0.3 Tariff Regime Module

The Tariff Regime Section (see Figure 3.18) offers deeper insights into
the duty regimes

applicable under different trade agreements. It visualizes preferential
agreements, MFN

rates, and partner-specific benefits across multiple years, supporting
complex multi-country

trade analysis.

> Figure 3.18: Duty Regime Visualization Displaying MFN and Preferential
> Agreements.
>
> 52

Chapter 3. Agentic AI Modeling and
Implementation<img src="./esgrid2v.png"
style="width:5.84641in;height:2.97248in" />

3.7.0.4 Price CNF Data Visualization

The Price CNF Table (see Figure 3.19) integrates tax regimes with CNF
(Cost and Freight)

prices, allowing users to observe post-tariff price impacts across
origins and destinations.

This table is particularly useful for trade negotiation simulations and
supplier risk assess-

ments.

> Figure 3.19: Price CNF Table: Combined Freight Costs and Tariff
> Impacts Across Origins and Countries.

3.7.0.5 CNF Trend Chart

The CNF Line Chart (see Figure 3.20) illustrates price evolutions over
time by plotting CNF

values both before and after tax adjustments. This enables rapid
identification of pricing

volatility, market disruptions, or supply chain fluctuations.

> 53

Chapter 3. Agentic AI Modeling and
Implementation<img src="./ggcbdwb4.png"
style="width:5.84641in;height:2.76328in" />

> Figure 3.20: Line Chart of CNF Price Trends Over Time With Tax
> Adjustments.

Conclusion

This chapter outlined the comprehensive technical and architectural
blueprint that enables

the TAXI platform to function as an advanced, autonomous system for
trading analytics. Its

hybrid architecture seamlessly integrates retrieval-augmented generation
(RAG), semantic

search indexing, real-time web search capabilities, and modular data
ingestion workflows, all

within a scalable and highly eficient local-first processing ecosystem.

> By employing cutting-edge components such as FAISS, ChromaDB,
> LangChain,

DeepSeek R1, DuckDuckGo, and Ollama, the platform transcends basic
database query-

ingtoperformcomplexreal-timereasoningoverlarge-scaleregulatoryandeconomicdatasets.

Its capacity to semantically process millions of data points, synthesize
multi-source knowl-

edge, and deliver highly detailed trade intelligence demonstrates a
sophisticated integration

of AI reasoning models, optimized backend storage engines, and rapid
retrieval systems.

> The user experience is further enhanced by the Gradio-based
> interactive interface, which

serves both as an administrative dashboard and an intuitive frontend for
end-users. Users

can seamlessly upload datasets, execute complex queries, and monitor all
reasoning processes

with full transparency. Advanced debugging functionalities reveal FAISS
vector similarities,

retrieved source documents, and complete reasoning chains for each
response.

> 54

Chapter 3. Agentic AI Modeling and Implementation

> Additionally, the analytical dashboard complements the agentic
> reasoning system by vi-

sually displaying tariff structures, CNF pricing models, duty regimes,
and international trade

trends across multiple commodities and regions. This interactive
visualization environment

bridges automated AI capabilities with expert human analysis, supporting
evidence-based

decision-making for trade, policy, and supply chain management.

> Ultimately, the TAXI Agentic AI platform is designed for high
> adaptability and rapid

expansion. Whether ingesting newly published regulatory frameworks,
analyzing dynamic

trade agreements, or simulating multi-layered tariff scenarios, it
maintains both precision

and transparency—essential characteristics for policy development,
market forecasting, and

global trade analysis.

> 55
>
> General Conclusion

This initiative introduces the innovative TAXI Agentic AI platform, an
entirely au-

tonomous system designed to interpret worldwide trade information, tax
laws, and policy

changes. Using advanced AI technology, high-speed data processing, and
intelligent data

retrieval, it provides a practical solution to navigate the complexities
of international com-

merce and regulations. The platform merges advanced technical tools with
an accessible

user interface, aiming to deliver valuable insights swiftly.

> Duringitsdevelopment,
> severalimportantscientificandtechnicalmilestoneswereachieved:
>
> • Automated Data Pipeline: A fully automated data pipeline was
> established to
>
> collect and process information from various sources, such as APIs
> from ITC, FedEx,
>
> and DNEXT, with web scraping managed through Dagster to ensure data
> integrity
>
> and accuracy.
>
> • Semantic Search and Reasoning: The system enhances semantic search
> and rea-
>
> soning capabilities using Sentence-Transformers and FAISS, allowing it
> to index mil-
>
> lions of data points based on their meaning for quick access. ChromaDB
> securely stores
>
> these data vectors, while DeepSeek R1, operated locally via Ollama,
> supports complex
>
> reasoning—interpreting both structured data and unstructured text in
> real time.
>
> • Real-Time Knowledge Fusion: By merging recent web searches from
> DuckDuckGo
>
> with historical data, TAXI provides up-to-date insights on policies,
> trade agreements,
>
> and geopolitical events, keeping users knowledgeable of the latest
> changes.
>
> • Multi-Layered Reasoning Architecture: Its multi-layered AI reasoning
> process
>
> enables the platform to perform thorough analysis, verify information,
> and synthesize
>
> knowledge for detailed trade forecasts, duty computations, and CNF
> evaluations with
>
> high reliability.
>
> • User Interface: The user interface, built using Gradio, allows easy
> file uploads, trou-
>
> bleshooting, and transparent explanations of reasoning processes. It
> supports smooth
>
> 56

General Conclusion

> updates to datasets without requiring system downtime or retraining.
>
> • Interactive Analytics Dashboard: A Power BI dashboard offers visual
> insights into
>
> tariffs, CNF prices, product taxes, and international trade flows.
> Users can interac-
>
> tively explore data with filters, trend analyses, and time series
> views.
>
> Beyond its technical innovations, the project provides a flexible
> framework to tackle real-

world issues such as trade compliance, customs procedures, and policy
analysis. The combi-

nation of modern AI, semantic understanding, and structured data
workflows demonstrates

how adaptable platforms can assist complex decision-making, merging
machine accuracy

with human interpretability.

> Future Perspectives:
>
> • Developing predictive tools for CNF, tax, and trade condition
> forecasts to enhance
>
> policy modeling.
>
> • Integrating OCR technologies to extract data directly from legal
> documents and reg-
>
> ulatory treaties, further deepening the system’s legal reasoning
> capacity.
>
> • Creating more autonomous AI agents capable of self-assessment,
> conflict resolution,
>
> and advanced multi-step reasoning to strengthen reasoning under
> uncertain conditions.
>
> • Transitioning TAXI to a scalable cloud environment to support
> broader adoption by
>
> enterprises, government bodies, and research groups.
>
> In summary, this project exemplifies how the fusion of AI, data
> engineering, and intel-

ligent retrieval can form an autonomous trade analysis platform. The
TAXI Agentic AI

system pushes technological boundaries and lays the groundwork for
future advancements

in trade intelligence, regulatory insights, and strategic
decision-making, with wide-ranging

implications across scientific, economic, and policy domains.

> 57
>
> Bibliography

\[1\] DNEXT Intelligence SA. Dnext solutions overview.
[https://www.dnext.io/](https://www.dnext.io/solutions/)

> [solutions/.](https://www.dnext.io/solutions/)

\[2\] CRISP-DM Consortium. Crisp-dm: The standard methodology for data
mining and

> analytics.
> [https://www.sv-europe.com/crisp-dm-methodology/.](https://www.sv-europe.com/crisp-dm-methodology/)

\[3\] Various Authors. Large language models (llm) limitations - google
search overview.

> [https://www.google.com/search?q=LLM+limitations,](https://www.google.com/search?q=LLM+limitations)
> 2025.

\[4\] Hugging Face. Retrieval-augmented generation (rag) with
smolagents.
[https://](https://huggingface.co/docs/smolagents/examples/rag)

> [huggingface.co/docs/smolagents/examples/rag,](https://huggingface.co/docs/smolagents/examples/rag)
> 2025.

\[5\] Substack Visual. Rag architecture diagram.
[https://substackcdn.com/](https://substackcdn.com/image/fetch/w_1200,h_600,c_fill,f_jpg,q_auto:good,fl_progressive:steep,g_auto/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Ff90434a2-7f75-4c16-8461-d1efed5939d0_1380x730.png)

> [image/fetch/w_1200,h_600,c_fill,f_jpg,q_auto:good,fl_progressive:](https://substackcdn.com/image/fetch/w_1200,h_600,c_fill,f_jpg,q_auto:good,fl_progressive:steep,g_auto/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Ff90434a2-7f75-4c16-8461-d1efed5939d0_1380x730.png)
>
> [steep,g_auto/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%](https://substackcdn.com/image/fetch/w_1200,h_600,c_fill,f_jpg,q_auto:good,fl_progressive:steep,g_auto/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Ff90434a2-7f75-4c16-8461-d1efed5939d0_1380x730.png)
>
> [2Fpublic%2Fimages%2Ff90434a2-7f75-4c16-8461-d1efed5939d0_1380x730.png,](https://substackcdn.com/image/fetch/w_1200,h_600,c_fill,f_jpg,q_auto:good,fl_progressive:steep,g_auto/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Ff90434a2-7f75-4c16-8461-d1efed5939d0_1380x730.png)
>
> 2025\.

\[6\] Langformers Blog. Semantic search: The foundation for modern ai
retrieval systems.

> [https://blog.langformers.com/semantic-search/,](https://blog.langformers.com/semantic-search/)
> 2025.

\[7\] Deepanshu Sachdeva. Understanding transformers step-by-step:

> Word embeddings.
> [https://deepanshusachdeva5.medium.com/](https://deepanshusachdeva5.medium.com/understanding-transformers-step-by-step-word-embeddings-4f4101e7c2f)
>
> [understanding-transformers-step-by-step-word-embeddings-4f4101e7c2f,](https://deepanshusachdeva5.medium.com/understanding-transformers-step-by-step-word-embeddings-4f4101e7c2f)
>
> 2020\.

\[8\] Hugging Face. Getting started with embeddings.
[https://huggingface.co/blog/](https://huggingface.co/blog/getting-started-with-embeddings)

> [getting-started-with-embeddings,](https://huggingface.co/blog/getting-started-with-embeddings)
> 2023.

\[9\] Google Images (Transformer Diagram). Transformer architecture vi-

> sualization.
> [https://encrypted-tbn0.gstatic.com/images?q=tbn:](https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS6N9CmtN5u98ZWQMyjHNa8WOz6P2sOMHoljg&s)
>
> [ANd9GcS6N9CmtN5u98ZWQMyjHNa8WOz6P2sOMHoljg&s.](https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS6N9CmtN5u98ZWQMyjHNa8WOz6P2sOMHoljg&s)
>
> I

Bibliography

\[10\] DeepSpeed AI Team. Deepspeed ai.
[https://www.deepspeed.ai/,](https://www.deepspeed.ai/) 2025.

\[11\] Ollama Team. Ollama python package.
[https://pypi.org/project/ollama/,](https://pypi.org/project/ollama/)
2025.

\[12\] LangChain Team. Langchain oficial website.
[https://www.langchain.com/,](https://www.langchain.com/) 2025.

\[13\] International Trade Centre. International trade centre (itc)
logo. Online Image.

\[14\] FedEx Corporation. Fedex oficial logo. Online Image.

\[15\] Dagster Labs. Dagster oficial logo. Online Image.

\[16\] Snowflake Inc. Snowflake oficial logo. Online Image.

\[17\] DeepSeek AI. Deepseek-r1 model on hugging face.
[https://huggingface.co/](https://huggingface.co/deepseek-ai/DeepSeek-R1)

> [deepseek-ai/DeepSeek-R1.](https://huggingface.co/deepseek-ai/DeepSeek-R1)

\[18\] Meta AI. Faiss: Facebook ai similarity search.
[https://ai.meta.com/tools/faiss/.](https://ai.meta.com/tools/faiss/)

\[19\] Masato Nakama. Enhancing langchain’s retrievalqa for

> real source links.
> [https://nakamasato.medium.com/](https://nakamasato.medium.com/enhancing-langchains-retrievalqa-for-real-source-links-53713c7d802a)
>
> [enhancing-langchains-retrievalqa-for-real-source-links-53713c7d802a,](https://nakamasato.medium.com/enhancing-langchains-retrievalqa-for-real-source-links-53713c7d802a)
>
> 2024\.

\[20\] ChromaDB Team. Chromadb logo. Image extracted from source data.

\[21\] DuckDuckGo Team. Duckduckgo logo.
[https://upload.wikimedia.org/wikipedia/](https://upload.wikimedia.org/wikipedia/fr/thumb/8/88/DuckDuckGo_logo.svg/2560px-DuckDuckGo_logo.svg.png)

> [fr/thumb/8/88/DuckDuckGo_logo.svg/2560px-DuckDuckGo_logo.svg.png.](https://upload.wikimedia.org/wikipedia/fr/thumb/8/88/DuckDuckGo_logo.svg/2560px-DuckDuckGo_logo.svg.png)

\[22\] DeepSpeed AI Team. Deepspeed logo. Retrieved from base64 image
data.

\[23\] Meta AI Team. Faiss: Facebook ai similarity search.
[https://ai.meta.com/tools/](https://ai.meta.com/tools/faiss/)

> [faiss/.](https://ai.meta.com/tools/faiss/)

\[24\] Diego Ferrer. Make large language models play nice with your
soft-

> ware: Langchain.
> [https://www.kdnuggets.com/wp-content/uploads/ferrer_make\_](https://www.kdnuggets.com/wp-content/uploads/ferrer_make_large_language_models_play_nice_software_langchain_2.png)
>
> [large_language_models_play_nice_software_langchain_2.png.](https://www.kdnuggets.com/wp-content/uploads/ferrer_make_large_language_models_play_nice_software_langchain_2.png)

\[25\] Microsoft Corporation. Power bi logo.
[https://klint-consulting.com/wp-content/](https://klint-consulting.com/wp-content/uploads/2023/04/Power-BI-Microsoft-logo.png)

> [uploads/2023/04/Power-BI-Microsoft-logo.png.](https://klint-consulting.com/wp-content/uploads/2023/04/Power-BI-Microsoft-logo.png)
>
> II

<img src="./wmmsrcog.png"
style="width:8.27014in;height:11.39597in" />**Abstract**

The TAXI platform is designed to develop a smart system that supports
professionals involved in international trade regulations by offering
automated data analysis and insights. The system uses advanced methods
such as Retrieval-Augmented Generation (RAG), semantic search
techniques, and real-time web data integration to collect, interpret,
and assess comprehensive information related to taxes, pricing
strategies, and legal standards from multiple sources. Using innovative
language models complemented by layered vector memory databases like
FAISS and ChromaDB, along with external search tools such as DuckDuckGo,
TAXIensures precise data retrieval, reliable reasoning,and detailed
source documentation. Finally, it enables policymakers and business
leaders to better grasp regulatory environments, optimize supply chain
management, and maintain compliance all while reducing needing extensive
manual review and scattered searches.

**Résumé**

L'objectif du taxi est de développer un système d'IA qui peut examiner
et contrôler le commerce mondial, et également calculer les taxes. Le
système utilise des techniques innovantes pour générer et améliorer les
données (RAG), ainsi que les recherches actuelles sur le sens et les
données Web, pour acquérir, organiser et analyser des informations
complexes sur les taxes, les prix et les règles provenant de diverses
sources.

Taxi utilise des modèles de langage avancés, des souvenirs vectoriels de
plusieurs niveaux (Faish, ChromAdb) et des couches de recherche externes
(DuckDuckgo) pour garantir qu'il peut récupérer des informations de
manière cohérenteetavec une traçabilité complète de la source. Cette
solution donne aux gestionnaires la possibilité d'expérimenter diverses
règles, de surveiller les approvisionnements et de garantir le respect
des normes sans nécessiter une grande quantité de travail manuel ni la
recherche d'informations dans diverses sources.
