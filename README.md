# World Controller

World Controller is a library of GUI Applications and APIs for creating and interacting with a JSON Database, geared towards the use of Large Language Models (LLMs) to generate large amounts of content in a structured format.

The main pillars of this library are:
- Allowing LLMs to easily contribute and refine content
- Scalable team sizes (both Human and AI) working on the same body of content
- Trackable and understandable changes to content over time
- Easy extraction of generated content into different formats

## Definitions

| Name | Description |
| :-- | :-- |
| Struct/Type | a user-defined collection of variables |
| Node/Instances | an instance of a Struct |
| Generator | a user-defined piece of python code that creates and modifies Nodes |
| Executor | the system that runs the Generators |

## How does it work?

1. Define Structs - to store data, we must first define some Structs. Let's say, for instance, that I want to create a bunch of people. The Struct defines what information is stored about each person. We might want to store a person's name, gender, height, eye color, and many more attributes.

2. Create Generators - now that we have defined what all gets stored per person, we need to actually create different people, each with their own set of variables. An instance of a Struct is called a Node, and Nodes are made using Generators. Once you start dealing with more complex Structs, it starts making less and less sense to Generate your Node all in 1 go, which is why Generators can arbitrarily modify existing Nodes, even if they did not create them. This allows for the spreading of responsability between Generators and allows more distributed contribution mechanisms - if you set things up right that is.

3. Run the Engine - now that everything is in place, the content engine can be cranked. Generators cen be run b Executors, which come in many forms. The main GUI application has a built-in Executor, but there is also a standalone headless version (TODO) and custom Executors can also be created.

## Limitations

The system is currently being built around a "1 interaction per repo" design. An interaction can either be modification of a World's design (modifying structs, adding generators, etc.) or the running of an Executor. With a little forethought, this can be designed around. For example, adding an integer called stage to each Struct and defining what content gets generated at each stage allows for multiple copies of the World to be checked out at once, all being contributed to simultaneously, but with each Executor running different Generators targeting unique stages as to avoid clashes.
