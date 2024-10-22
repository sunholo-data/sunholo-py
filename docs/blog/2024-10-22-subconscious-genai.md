---
title: "Why GenAI Needs a Subconscious: Internal Monologues for your Cognitive Designs"
authors: me
tags: [agents, cognitive-design]
image: https://dev.sunholo.com/assets/images/cognitive-design-ec3719c6b00a22113dd45194210067fa.webp
slug: /subconscious-genai
---

A cognitive design I’ve come across recently apes the subconscious messages we have in our own brains, as distinct from inner monologue or stuff we say. Referencing our own way of thinking has revealed to me insight about how to improve GenAI functionality, as well as revealing back to me new insights into how we ourselves think.  I'm a distinct amateur in neuroscience, so I hope if I blog this someone more informed could perhaps comment on the approach outlined below, but I am finding it a very useful technique.

For this explanation, I break down cognition into three modes:

* What we say to others - e.g. us talking.  I attribute this in GenAI to a bot's output, like chat text.
* Our inner monologue - e.g. using our language for internal thoughts.  I attribute this to logging messages passed within the GenAI functions but not exposed to the end user.
* Our subconscious - e.g. thoughts we are not aware of, but influence our thoughts.  I attribute this to internal logging and messages within a GenAI function, that are not surfaced to an outer agent.  

I believe the messages passed around within a cognitive design can be broken out into the sub-categories above, and that can help us design better performing systems.  This seems to become important when one starts to work with asynchronous, parrallel calls to GenAI models, which again I think may be because that is more akin to how human brains work, rather than sequential, one at a time API calls we start with when first using GenAI models.

## Cognitive design and agent orchestration.

Using the above approach, I've created a chat bot that takes in various contexts and responds well to a variety of questions. It responds quickly, but as it is answering internal monologue and subsciousness influence and evolve the answer as its writing, until the reply ends with a reflective summary on everything it has just said. Note this is distinct from prompting techniques such as ReACT or Chain of Thought, which rely on a sequential, single API call.  A parallel approach for calling GenAI models means working at a more GenOps or data engineering level, aggregating API requests to GenAI models and orchestrating their parrallel returns via async or microservice patterns.

For a while now I've been thinking about how I could apply the principles in [Daniel Kahneman's Thinking Fast and Slow](https://www.amazon.com/Thinking-Fast-Slow-Daniel-Kahneman/dp/0374533555) book, which introduces "System 1" (fast) and "System 2" (slow) thinking.  Both ways of thinking have their usefulness, and making convincing GenAI bots that incorporate the same feels like a good route to making better bots.

I’m not a big believer in "AGI" if defined as a machine that can create novel new reasoning not in its training set or possessing internal qualia, but I do think large language models are going to be fantastically useful in surfacing all of human expression. We already see how metacognition techniques seem to help performance of agents at a prompt level (e.g. chain of thought). If copying mental patterns such as System 1/2 visibly help a silicon based agent, it’s a fascinating question why thats the case and worth exploring. 

## Inner monologue vs Subconscious Messaging

I’ve come across the need for subconscious messages when dealing with orchestrating several models in parallel which then feed into an orchestrator agent taking their output and summarising it.

My current cognitive design is shown below:

Agent tools are started in parallel and those tools contain LLMs to parse and decide on the usefulness of their output. Some return quickly such as as Google search bot, some can take a minute or so such as when it calls another agent that loops through database documents to examine them for suitability. 

The agents stream their responses as soon as they are available to the orchestrator agent, which then formulates the answer to the end user.   The replies and summary are all different API calls but the models are asked to continue responses as if they are replying with one voice via prompting, with conditions to not repeat oneself or to point out contradictions other sources may have surfaced. 

Anthropic's API implementation supports this explicitly, here is an example prompt:

:::note[Prompt]
My answer so far: `<response_so_far>`.  
I will continue my answer below, making sure I don't repeat any points already made. 
It may be that my answer below will contradict earlier answers, now I have more information and context.  
That is ok, I will just point it out and give an assessment on which context is more reliable. 
My continuing answer:
:::

Its written in the first person as if the agent is just continuing an existing answer.

The `<response_so_far>` is a string that is populated and grows longer each time a tool, bit of context or new information becomes available.  A loop over the responses repeatedly calls the prompt above, with longer and longer `<response_so_far>` content.

However, the end user is not seeing seperate API responses - instead those responses go to a callback queue, which streams the results to the user in one continuous answer.  This way we get system 1 style answers with quick initial responses based on limited information and then a longer more reflective system 2 answer near the end of the same answer, once all context is gathered. 

## Subconscious = stderr?

The subconscious messages I refer to are those that feed into each agent internally. There is a difference between what the user may want to read via what the model returns. Another more techy and less whimsical name would be `stderr`, if you're familiar with programming's [standard streams](https://en.wikipedia.org/wiki/Standard_streams). 

Similarly, the conscious messages are those surfaced directly to the user, or you could call it `stdout`.  

The function of these message types differ: the system-to-system, `stderr` or subconscious messages are more functional, and can just be large data dumps, JSON objects or logs not readable by a user.  The output intended for the end user, or `stdout` need to be curated: the job of the GenAI agent now is to extract order from their chaos, to bring structure and reason to the messages so a user can digest them.

## Turning subconscious into conscious

The reason I’m reaching for more provocative names for these messages is that it occurred to me that calling them subconscious or conscious messages is more just a matter of perspective once you have any level of nested hierarchy. If an agent uses a tool, that calls another agent, that in turn calls another agent, what should be surfaced to the end user differs accordingly. 

For example: a user requests a perspective on wind farms: an agent calls an energy database research agent which in turn calls a SQL creation agent. Internal (subconscious) messages may be the SQL fed to the database agent: the end user need not see it. The end user recieves a well considered answer that includes the results of the SQL, but doesn't see the SQL itself.

But next, a user requests the SQL to search the database themselves.  Now that previously subconscious SQL string should bubble up and be given to the user.  What was previously an inner internal message for bot use only should now reach external eyes.

Here I think is a key difference for GenAI systems over traditional software engineering.  The category of messages for external, internal and system level systems is more fluid: in some cases deep internal (subconscious) messages will need to be made available all the way to the end user; in other cases those messages can remain safely hidden, and in fact should be suppressed to stop overwhelming the user with useless details.

## Abstracting up to society and down to metabolism

The thing is, why stop there? The end user may be requesting the information from the bot to send to their manager so they can send it to a client. The client won’t need to know the details, and will probably just get the synopsis from the manager. Internal communication transparency is not wanted as it would cloud the insights. Isn't all human behaviour actually a plethora of choices between what internal messages are used to influence extrnal communication?

And in the other direction: as I type out words into this computer as directed by my internal monologue, the subconscious movement of my fingers is governed by processes I don’t need to know about. I can't ever get the details about how my fingers learnt to type, a physical memory that I did once consciously learn but is now so automatic it will be only be if I have brain injury that I will need to relearn it.

It ends up, we are talking about emergence, and how internal vs external communication play a pivotal role in that process.  Since GenAI models are incredibly complex representations of human expression, I think part of why its beckoning in a new age is that we are seeing emergent properties come from them.  And since emergent systems are loosely coupled to the distinct internal processes they are made of, its worth thinking about how and what those messages are.

## Applications to Cognitive Design

Bringing this back to practical points, I believe thinking about these messages can be applied in improving our cognitive designs.  If models, vectorstores, databases, users are the nodes, the messages between those systems are the edges.

My first applications after thinking about this are the following steps:

* To aid separation of these two message streams, create callback for the user (conscious) and a callback for internal messages (subconscious). There is no real reason to restrict this to two, but let’s keep it simple until we see a need for more.
* Let the models decide which stream to use. The cognitive architecture gains a free channel to send messages not intended for users (eg document metadata, download urls) and a channel for the end user. 
* Consider agent hierachies and how much information is sent to each level.  A sub-agent may only send/recieve what they need to function with no knowledge of the wider goal, or it could get more context so it can craft its answer better, and send back more information.  Probably good reasons for both strategies.
* Today's end user could in the future be a super-agent calling the same agent our current user needs.
* Individual agents don't need to be super-smart to contribute to a wider system.  Cheap/fast/dumb agents that do one thing well and in parallel with good messaging may outperform one expensive/slow/smart agent.  
* Monitor all messages effectively with evals, tracing, logs etc. and have an easy mechanism to move them between streams

## Ethics

One fear of the AI-led world is that machines will start to make decisions for us, in some neo-fascist world that does not value human diginity above other goals given to it or created internally by some twisted machine logic.  Having oversight on the internal messaging of GenAI systems then will play a critical importance to how these systems interface with humans and societies.  Measures such as GDPR and the AI Act in the EU are designed to never allow machines to change our fates without our knowledge.  The abuses of power like this predates AI by millennia, but we have a chance now to put in place adequete transparency in a way we couldn't actually do before: bureaucrats deciding the fates of people behind closed doors and via whispered conversations should be much harder to monitor than AI systems that are inherently digital and so should be able to have all internal thoughts, subconscious or otherwise, recorded and available at some level.  That neural nets are essentially blackbox in how they have assigned their internal weights should make it even more important to record and monitor every interaction that model creates.  For instance, every conversation my bots make are saved to a BigQuery database in cold storage, just in case.  But beyond simple monitoring, that dataset is the route to improving outcomes, as well as given people the trust on what these systems think, do and say.

## Future trends up to GenAI societies

And as I speculated about before, once we get to teams of agents then having an orchestrator agent with good leadership skills may be more important than a super-smart one.  The ability to clearly define goals, keep the bots motiviated(!) and allocate workloads effectively, and all skills not necessarily found in STEM, but in management and people skills.

I can see a future where just as software engineering gains abstractions (binary, assembly, system programming, dyanamic etc) the agents we make today may in the future be just one cog in a much larger system e.g. Multivac? :)  Having a route for deeply nested agents performing not just as single agents but groups, societies, companies and organizations with varying levels of internal and external messaging.

If you have some thoughts about the above, please let me know on social media or otherwise, I'm keen to hear your perspective too.  Have I stretched an analogy too far or can you see other applications of subsciousness in your GenAI system?  Let me know!
