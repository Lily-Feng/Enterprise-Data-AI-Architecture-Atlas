Advanced Data Engineering with Databricks
This course serves as an appropriate entry point to learn Advanced Data Engineering with Databricks. 



Note: Databricks Academy is transitioning to a notebook-based format for classroom sessions within the Databricks environment, discontinuing the use of slide decks for lectures in the first and fourth module. You can access the lecture notebooks in the Vocareum lab environment.



Below, we describe each of the four, four-hour modules included in this course.

Advanced Techniques with Spark Declarative Pipelines

This course explores Databricks' Apache Spark Declarative Pipelines (SDP) for building production-grade streaming pipelines. You will learn advanced design patterns, robust data quality enforcement, and cross-platform integration essential for real-world lakehouse engineering.



Throughout the course, you will dive into modern data ingestion and processing techniques, mastering tools like Liquid Clustering for layout optimization and the Multiplex Streaming pattern for mixed-schema events. By the end of the modules, you will know how to confidently handle schema evolution, automate Change Data Capture (CDC), and ensure data integrity.



Through lectures and hands-on demos, you will:

• Build multi-flow pipelines to ingest multi-source data into a unified Bronze table.

• Apply Liquid Clustering and Data Quality Expectations across Silver and Gold layers.

• Implement the Multiplex pattern with Iceberg UniForm for cross-platform data access.

• Automate SCD Type 2 history tracking using AUTO CDC INTO.

• Design zero-data-loss quarantine pipelines to audit and manage invalid records.



Databricks Data Privacy

This content is intended for the learner persona of data engineers or for customers, partners, and employees who complete data engineering tasks with Databricks. It aims to provide them with the necessary knowledge and skills to execute these activities effectively on the Databricks platform.



Databricks Performance Optimization

In this course, you’ll learn how to optimize workloads and physical layout with Spark and Delta Lake and and analyze the Spark UI to assess performance and debug applications. We’ll cover topics like streaming, liquid clustering, data skipping, caching, photons, and more.



Automated Deployment with Declarative Automation Bundles

This course provides a comprehensive review of DevOps principles and their application to Databricks projects. It begins with an overview of core DevOps, DataOps, continuous integration (CI), continuous deployment (CD), and testing, and explores how these principles can be applied to data engineering pipelines.

The course then focuses on continuous deployment within the CI/CD process, examining tools like the Databricks REST API, SDK, and CLI for project deployment. You will learn about Declarative Automation Bundles (DABs) and how they fit into the CI/CD process. You’ll dive into their key components, folder structure, and how they streamline deployment across various target environments in Databricks. You will also learn how to add variables, modify, validate, deploy, and execute Declarative Automation Bundles for multiple environments with different configurations using the Databricks CLI.

Finally, the course introduces Visual Studio Code as an Interactive Development Environment (IDE) for building, testing, and deploying Declarative Automation Bundles locally, optimizing your development process. The course concludes with an introduction to automating deployment pipelines using GitHub Actions to enhance the CI/CD workflow with Declarative Automation Bundles.

By the end of this course, you will be equipped to automate Databricks project deployments with Declarative Automation Bundles, improving efficiency through DevOps practices.



Languages Available: English | 日本語 | Português BR | 한국어


Skill Level
Professional
Duration
16h
Prerequisites
Prerequisites

• Spark Declarative Pipelines — Completion of the "Build Data Pipelines with Apache Spark Declarative Pipelines" course, or familiarity with CREATE OR REFRESH STREAMING TABLE, CONSTRAINTS, and the Pipelines UI

• Delta Lake Fundamentals — Understanding of Delta tables and how Delta manages data files and transaction logs

• Streaming Concepts — Knowledge of micro-batch streaming, checkpointing, and event-time processing in SDP

• SQL Proficiency — Ability to read and write SQL, including SELECT, JOIN, MERGE, CASE WHEN, and common aggregate functions

• Python in Databricks Notebooks — Comfort with reading and running Python code in Databricks notebooks

• Unity Catalog Basics — Understanding of catalogs, schemas, tables, and volumes in Unity Catalog

• Ability to perform basic code development tasks using the Databricks Data Engineering and Data Science workspace (create clusters, run code in notebooks, use basic notebook operations, import repos from git, etc.)

• Intermediate programming experience with PySpark

• Extract data from a variety of file formats and data sources

• Apply a number of common transformations to clean data

• Reshape and manipulate complex data using advanced built-in functions

• Intermediate programming experience with Delta Lake (create tables, perform complete and incremental updates, compact files, restore previous versions, etc.) 

• Beginner experience configuring and scheduling data pipelines using the Apache Spark Declarative Pipelines UI 

• Beginner experience defining Apache Spark Declarative Pipelines using PySpark 

• Ingest and process data using Auto Loader and PySpark syntax

• Process Change Data Capture feeds with APPLY CHANGES INTO syntax

• Review pipeline event logs and results to troubleshoot Declarative Pipeline syntax

• Strong knowledge of the Databricks platform, including experience with Databricks Workspaces, Apache Spark, Delta Lake, the Medallion Architecture, Unity Catalog, Apache Declarative Pipelines, and Workflows. In particular, knowledge of leveraging Expectations with Apache Declarative Pipelines. 

• Experience in data ingestion and transformation, with proficiency in PySpark for data processing and DataFrame manipulation. Candidates should also have experience writing intermediate-level SQL queries for data analysis and transformation.

• Proficiency in Python programming, including the ability to design and implement functions and classes, and experience with creating, importing, and utilizing Python packages.

• Familiarity with DevOps practices, particularly continuous integration and continuous delivery/deployment (CI/CD) principles.

• A basic understanding of Git version control.

• Prerequisite course DevOps Essentials for Data Engineering Course

Outline
Advanced Techniques with Apache Spark Declarative Pipelines

• Introduction to Multi Flows, Expectation and Liquid Clustering in SDP

• Demo: Multi Flow SDP with Liquid Clustering and Data Quality

• Introduction to Multiplex Streaming, Delta Sinks and  Iceberg Reads

• Demo: Multiplex Streaming SDP with Delta Sinks and Iceberg Reads

• Change Data Capture (CDC) Review

• Demo: Automating SCD Type 2 with AUTO CDC in Apache Spark Declarative Pipelines

• Advanced Data Quality Checks and Expectations in SDP

• Demo: Advanced Data Quality Checks and Expectation in SDP

• Lab - Building Multi-Source Ecommerce Pipeline with SDP



Databricks Data Privacy

• Regulatory Compliance

• Data Privacy

• Key Concepts and Components

• Audit Your Data

• Data Isolation

• Demo: Securing Data in Unity Catalog 

• Pseudonymization & Anonymization

• Summary & Best Practices

• Demo: PII Data Security

• Capturing Changed Data

• Deleting Data in Databricks

• Demo: Processing Records from CDF and Propagating Changes

• Lab: Propagating Changes with CDF Lab



Databricks Performance Optimization

• DevOps Spark UI Introduction

• Introduction to Designing Foundation

• Demo: File Explosion

• Data Skipping and Liquid Clustering

• Lab: Data Skipping and Liquid Clustering

• Skew

• Shuffles

• Demo: Shuffle

• Spill

• Lab: Exploding Join

• Serialization

• Demo: User-Defined Functions

• Fine-Tuning: Choosing the Right Cluster

• Pick the Best Instance Types



Automated Deployment with Declarative Automation Bundles

• DevOps Review

• Continuous Integration and Continuous Deployment/Delivery (CI/CD) Review

• Demo: Course Setup and Authentication

• Deploying Databricks Projects

• Introduction to Declarative Automation Bundles (DABs)

• Demo: Deploying a Simple DAB

• Lab: Deploying a Simple DAB

• Variable Substitutions in DABs

• Demo: Deploying a DAB to Multiple Environments

• Lab: Deploy a DAB to Multiple Environments

• DAB Project Templates Overview

• Lab: Use a Databricks Default DAB Template

• CI/CD Project Overview with DABs

• Demo: Continuous Integration and Continuous Deployment with DABs

• Lab: Adding ML to Engineering Workflows with DABs

• Developing Locally with Visual Studio Code (VSCode)

• Demo: Using VSCode with Databricks

• CI/CD Best Practices for Data Engineering

• Next Steps: Automated Deployment with GitHub Actions