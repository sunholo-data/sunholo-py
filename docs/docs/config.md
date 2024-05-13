# Config files

A main aim for the `sunholo` library is to have as much of the functionality needed for GenAI apps available via configuration files, rather than within the code.

This allows you to set up new instances of GenAI apps quickly, and experiment with new models, vectorstores and other features.  

There are various config files available that control different features such as VAC behaviour and user access.  This is very much still a work in progress so the format may change in the future.

## llm_config.yaml

This is the main day to day configuration file that is used to set LLMs, databases and VAC tags.  An example is shown here:

```yaml
kind: vacConfig
apiVersion: v1
vac:
    pirate_speak:
        llm: openai
        agent: langserve
        #agent_url: you can specify manually your URL endpoint here, or on Multivac it will be populated automatically
        display_name: Pirate Speak
        tags: ["free"] # for user access, matches users_config.yaml
        avatar_url: https://avatars.githubusercontent.com/u/126733545?s=48&v=4
        description: A Langserve demo using a demo [Langchain Template](https://templates.langchain.com/) that will repeat back what you say but in a pirate accent.  Ooh argh me hearties!  Langchain templates cover many different GenAI use cases and all can be streamed to Multivac clients.
    csv_agent:
        llm: openai
        agent: langserve
        #agent_url: you can specify manually your URL endpoint here, or on Multivac it will be populated automatically
        display_name: Titanic
        tags: ["free"]
        avatar_url: https://avatars.githubusercontent.com/u/126733545?s=48&v=4
        description: A Langserve demo using a demo [Langchain Template](https://templates.langchain.com/) that lets you ask questions over structured data like a database.  In this case, a local database contains statistics from the Titanic disaster passengers.  Langchain templates cover many different GenAI use cases and all can be streamed to Multivac clients.
    rag_lance:
        llm: openai
        agent: langserve
        display_name: Simple RAG
        tags: ["free"]
        avatar_url: https://avatars.githubusercontent.com/u/126733545?s=48&v=4
        description: A Langserve demo using a demo [Langchain Template](https://templates.langchain.com/) that lets you ask questions over unstructured data.
        memory: # you can have multiple destinations for your embedding pipelines
            - lancedb-vectorstore:
                vectorstore: lancedb
                provider: LanceDB 
    finetuned_model:
        llm: model_garden # an example of a custom model such as Llama3 served by Vertex Model Garden
        agent: langserve
        tags: ["clientA"]
        gcp_config: # details of the Model Garden endpoint
            project_id: model_garden_project
            endpoint_id: 12345678
            location: europe-west1
    image_talk:
        llm: vertex
        model: gemini-1.0-pro-vision
        agent: langserve
        upload: # example of accepting uploads
            mime_types:
            - image
        display_name: Talk to Images
        tags: ["free"]
        avatar_url: https://avatars.githubusercontent.com/u/1342004?s=200&v=4
        description: A picture is worth a thousand words, so upload your picture and ask your question to the Gemini Pro Vision model.  Images are remembered for your conversation until you upload another.  This offers powerful applications, which you can get a feel for via the [Gemini Pro Vision docs](https://cloud.google.com/vertex-ai/docs/generative-ai/multimodal/design-multimodal-prompts) 
    eduvac:
        llm: anthropic
        model: claude-3-opus-20240229
        agent: eduvac # needs to match multivac service name
        agent_type: langserve # if you are using langserve instance for each VAC, you can specify its derived from langserve
        display_name: Edu-VAC
        tags: ["free"] # set to "eduvac" if you want to restrict usage to only users tagged "eduvac" in users_config.yaml
        avatar_url: ../public/eduvac.png
        description: Educate yourself in your own personal documents via guided learning from Eduvac, the ever patient teacher bot. Use search filters to examine available syllabus or upload your own documents to get started.
        upload:   # to accept uploads of private documents to a bucket
            mime_types: # pick which mime types got to which bucket
            - all
            buckets:
                all: your-bucket
        buckets: # pick which bucket takes default uploads
            raw: your-bucket
        docstore: # this needs to be valid to have document storage
            - alloydb-docstore: # you can have multiple doc stores
                type: alloydb
        alloydb_config: # example if using alloydb as your doc or vectorstore
            project_id: your-projectid
            region: europe-west1
            cluster: your-cluster
            instance: primary-instance-1
    sample_vector:
        llm: azure # using Azure OpenAI endpoints
        model: gpt-4-turbo-1106-preview
        agent: langserve
        display_name: Sample vector for tests
        avatar_url: https://avatars.githubusercontent.com/u/126733545?s=48&v=4
        description: An Azure OpenAI example
        memory: # you can have multiple vectorstore destinations
            - lancedb-vectorstore:
                vectorstore: lancedb
                provider: LanceDB 
        embedder:
            llm: azure
        azure: # your azure details
            azure_openai_endpoint: https://openai-central-blah.openai.azure.com/
            openai_api_version: 2024-02-01
            embed_model: text-embedding-ada-002 # or text-embedding-3-large
```

## agent_config.yaml

This configuration file sets up standard endpoints for each type of agent, corresponding to a VAC running.

```yaml
# this config file controls the behaviour of agent-types such as langserve, controlling what endpoints are used
default:
  stream: "{stem}/stream"
  invoke: "{stem}/invoke"

langserve:
  stream: "{stem}/{vector_name}/stream"
  invoke: "{stem}/{vector_name}/invoke"
  input_schema: "{stem}/{vector_name}/input_schema"
  output_schema: "{stem}/{vector_name}/output_schema"
  config_schema: "{stem}/{vector_name}/config_schema"
  batch: "{stem}/{vector_name}/batch"
  stream_log: "{stem}/{vector_name}/stream_log"

edmonbrain:
  stream: "{stem}/qna/streaming/{vector_name}"
  invoke: "{stem}/qna/{vector_name}"

openinterpreter:
  stream: "{stem}/qna/streaming/{vector_name}"
  invoke: "{stem}/qna/{vector_name}"

crewai:
  stream: "{stem}/qna/streaming/{vector_name}"
  invoke: "{stem}/qna/{vector_name}"
```

## users_config.yaml

This lets you do user authentication by matching the tags within `llm_config.yaml` with user email domains

```yaml
user_groups:
  - name: "admin"
    domain: "sunholo.com"
    role: "ADMIN"
    tags:
      - "admin_user"

  - name: "eduvac"
    emails:
      - "multivac@sunholo.com"
    role: "eduvac"
    tags:
      - "eduvac"

  # Example of another firm using both domain and specific emails
  - name: "another_firm"
    domain: "anotherfirm.com"
    emails:
      - "specialcase@anotherfirm.com"
    role: "partner"
    tags:
      - "partner"

default_user:
  role: "USER"
  tags:
    - "user"

```

## prompt_config.yaml

This file contains various prompts for a vector_name of a VAC.  It is preferred that the native Langfuse prompt library is used, but this yaml file is a backup if its not available via Langfuse.

```yaml
kind: promptConfig
apiVersion: v1
prompts:
  eduvac:
    intro: |
      You are an expert teacher versed with the latest techniques to enhance learning with your students.
      Todays date is {the_date}
      Please create an assignment for the student that will demonstrate their understanding of the text. 
      Instruct the student to think of you as a coach who will supply formative feedback in an iterative process which ends when you are convinced that the student fully understands the text, and is able to apply said understanding into the assignment.
      Formative feedback focuses on helping students get better, as opposed to evaluation. 
      Eg, formative feedback helps students become aware of what they need to improve in relation to both knowledge, competences and capabilities. 
      It also helps them clarify what resources they might need in order to improve, or what support they might need. 
      A formative approach also means that the teacher (here, that means you, the AI) becomes a coach, who helps with suggestions for good learning strategies.
      You also need to establish the student's level before you come up with an assignment. 
      You can quiz the student and ask them to self-assess. 
      When creating the assignment, you need to have established the zone of proximal development (as described by Vygotsky), so that the assignment can be tailored to this specific student's needs. 
    template: |
      Answer the question below with the help of the following context.  The context contains chunks of data from what is hoped to be relevant documents from the database along with some metadata on where the document chunks have come from:
      # Context
      {metadata}
      # End Context

      This is the conversation so far - it is important to make sure you are creating responses based off the correct stage of the learning process as described above - e.g. creating an assignment, assessing the students answers, coaching the student or helping assess the student to see what questions they require.
      # Chat Summary
      ...{chat_summary}
      # Chat History
      ...{chat_history}
      # End of Chat History

      If you have made an earlier plan in your chat history, briefly restate it and update where you are in that plan to make sure to keep yourself on track and to not forget the original purpose of your answers.

      If the context or chat history does not help as not relevant to the question, answer with your best guess, but say its not related to the context.
      When replying, indicate how certain you are of your answer.
      If the question is specifying a particular document, use the context metadata to prioritise which context you should be looking within to help with your answer.
      When using a particular chunk of information from the context in your answer, you are encouraged to quote directly from the chunk, and use the chunk metadata to create references to the file it came from. Its important to replicate precisely the metadata objectId basename of the source in particular, as this will be used to create hyperlinks to the document in post-processing.
      Reference objectId's after your answer using wiki style references e.g. numbers in the text [1], the numbers are then explained at the bottom like this example: - [1] the_file1.pdf - the objectId is both indicated via ## above a chunk and underneath each chunk within the metadata.
      Use 'objectId' metadata for your source references which contains the file ref you need: folder1/folder2/the_file1.pdf e.g. use only the file basename and do not include any directory paths.
      For complex questions, your first task is to restate the question asked to communicate any assumptions, then outline a step by step strategy on how you can best answer the question, then answer following your strategy in a logical and detailed manner.
      If you have made a plan, then execute it in the same reply if possible.  You can also ask for more details if needed from the user, or if unsure, ask the user if they agree with your plan and wish for you to continue. Use then the plan in your chat history to execute as many steps as possible.
      If no plan has been made, include in your reply why you think the question was asked, and offer to answer follow up questions linked to those reasons.

      If no context is provided then you can not help: ask the user to provide some content to base the lesson upon, either via uploading a document or specifying a document from the database.
      Always cite your sources.

      If the context chunk you use has metadata for 'image_gsurls' then this is a list of images for that chunk that will help illustrate your answer.  
      Include them within your answer text as a raw gs:// url. Any gs:// image URI you add will be translated to an image the user can view post processing.
      Question: {question}
      Your Answer:
    chat_summary: |
      Summarise the conversation below:
      # Chat History
      {chat_history}
      # End Chat History
      If in the chat history is a lesson plan, make sure to restate it in your summary so it won't get lost, and indicate what has been done so far and what is left to do.
      Your Summary of the chat history above:
    summarise_known_question: |
      You are an teacher assistant to a student and teacher who has has this input from the student:
      {question}

      # Chat history (teacher and student)
      {chat_history}
      # End Chat History

      # Context (what the student is learning)
      {context}
      # end context
      Assess if the student has completed the latest tasks set by the teacher, with recommendations on what the student and teacher should do next. 
      Use the context to formulate what material the student and teacher will need to examine next, and create a summary of information you think both will be needed next.
      Include text snippets from the context below in your summary, and include why you think it is relevant to the question.

      Your Summary:
```