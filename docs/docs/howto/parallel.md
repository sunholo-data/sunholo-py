# Parallel Execution

In many cases in GenAI its useful to call GenAI models or functions in parallel, to speed up user experience of the response.

A basic `asyncio` powered class is available via `AsyncTaskRunner` to help facilitate this, primarily intended for API calls to VACs and agents.

It will wait for the first function to return and get the full result, before waiting for the next etc.   This is useful when constructing lots of context from different agents to feed into an orchestrator agent.

```python
import asyncio
from sunholo.invoke import AsyncTaskRunner
from sunholo.vertex import init_vertex, vertex_safety
from vertexai.preview.generative_models import GenerativeModel

async def do_async(question):
    # Initialize Vertex AI
    init_vertex(location="europe-west1")
    runner = AsyncTaskRunner(retry_enabled=True)

    # Define async functions for runner
    async def english(question):
        print(f"This is English: question='{question}'")
        model = GenerativeModel(
            model_name="gemini-1.5-flash",
            safety_settings=vertex_safety(),
            system_instruction="Answer in English"
        )
        result = await model.generate_content_async(question)
        return result.text  # Assuming result has a 'text' attribute

    async def danish(question):
        print(f"This is Danish: question='{question}'")
        model = GenerativeModel(
            model_name="gemini-1.5-flash",
            safety_settings=vertex_safety(),
            system_instruction="Answer in Danish"
        )
        result = await model.generate_content_async(question)
        return result.text

    async def french(question):
        print(f"This is French: question='{question}'")
        model = GenerativeModel(
            model_name="gemini-1.5-flash",
            safety_settings=vertex_safety(),
            system_instruction="Answer in French"
        )
        result = await model.generate_content_async(question)
        return result.text

    async def italian(question):
        print(f"This is Italian: question='{question}'")
        model = GenerativeModel(
            model_name="gemini-1.5-flash",
            safety_settings=vertex_safety(),
            system_instruction="Answer in Italian"
        )
        result = await model.generate_content_async(question)
        return result.text

    # Add tasks to the runner
    runner.add_task(english, question)
    runner.add_task(french, question)
    runner.add_task(danish, question)
    runner.add_task(italian, question)

    # Run tasks and process results as they complete
    answers = {}
    print(f"Start async run with {len(runner.tasks)} runners")
    async for result_dict in runner.run_async_as_completed():
        for func_name, result in result_dict.items():
            if isinstance(result, Exception):
                print(f"ERROR in {func_name}: {str(result)}")
            else:
                # Output the result
                print(f"{func_name.capitalize()} answer:")
                print(result)
                answers[func_name] = result

    # Return a dict of the results {"english": ..., "french": ..., "danish": ..., "italian": ...}
    return answers

# Run the asynchronous function
if __name__ == "__main__":
    question = "What is MLOps?"

    # Run the do_async function using asyncio.run
    answers = asyncio.run(do_async(question))

    print("\nFinal answers:")
    for language, answer in answers.items():
        print(f"{language.capitalize()}:\n{answer}\n")
```


Gives results like this in a couple of seconds:

```
2024-09-17 16:59:54,297 - sunholo - INFO - Adding task: english with args: ('What is MLOps?',)
2024-09-17 16:59:54,297 - sunholo - INFO - Adding task: french with args: ('What is MLOps?',)
2024-09-17 16:59:54,297 - sunholo - INFO - Adding task: danish with args: ('What is MLOps?',)
2024-09-17 16:59:54,297 - sunholo - INFO - Adding task: italian with args: ('What is MLOps?',)
Start async run with 4 runners
2024-09-17 16:59:54,297 - sunholo - INFO - Running tasks asynchronously and yielding results as they complete
2024-09-17 16:59:54,297 - sunholo - INFO - Start async run with 4 runners
This is English: question='What is MLOps?'
This is French: question='What is MLOps?'
This is Danish: question='What is MLOps?'
This is Italian: question='What is MLOps?'
Italian answer:
MLOps è un insieme di pratiche e tecnologie che consentono di sviluppare, distribuire e gestire i modelli di machine learning (ML) in modo efficiente e affidabile. In pratica, si tratta di applicare i principi DevOps al mondo del machine learning, automatizzando i processi e rendendo più facile la collaborazione tra data scientist, ingegneri e team aziendali.

Ecco alcuni aspetti chiave di MLOps:

* **Integrazione continua e consegna continua (CI/CD) per i modelli ML:**  automazione del processo di sviluppo, test e distribuzione dei modelli, rendendolo più veloce e affidabile.
* **Gestione del ciclo di vita del modello:**  monitoraggio delle prestazioni del modello nel tempo, identificazione delle aree di miglioramento e riaddestramento quando necessario.
* **Collaborazione:**  facilitazione della collaborazione tra team diversi, garantendo la condivisione di risorse, codice e dati.
* **Infrastruttura scalabile:**  fornitura di un'infrastruttura che possa gestire facilmente l'aumento del volume di dati e delle richieste di elaborazione.
* **Sicurezza e privacy:**  applicazione di pratiche di sicurezza e privacy per proteggere i dati e i modelli.

In sostanza, MLOps aiuta a portare il machine learning dal mondo della ricerca a quello della produzione, rendendolo un processo continuo e iterativo.

French answer:
**MLOps** est un ensemble de pratiques qui visent à automatiser et à industrialiser le cycle de vie complet du machine learning (ML), de la conception à la production. 

En d'autres termes, MLOps permet de mettre en place des processus robustes et efficaces pour développer, déployer et gérer des modèles ML à l'échelle.

**Voici quelques-uns des principaux aspects de MLOps :**

* **Automatisation:** MLOps automatise les tâches répétitives telles que la préparation des données, l'entraînement des modèles, le déploiement et la surveillance.
* **Collaboration:** MLOps facilite la collaboration entre les équipes de data science, d'ingénierie et d'opérations.
* **Gestion du cycle de vie:** MLOps couvre toutes les étapes du cycle de vie ML, de la conception à la production, en passant par le développement et la maintenance.
* **Surveillance et itérations:** MLOps permet de suivre les performances des modèles et de les mettre à jour régulièrement pour assurer leur exactitude et leur fiabilité.

**Les avantages de MLOps incluent :**

* Accélération du développement et du déploiement de modèles ML.
* Amélioration de la fiabilité et de la qualité des modèles.
* Réduction des coûts et des efforts associés à la gestion des modèles.
* Facilitation de la collaboration entre les équipes.

**En résumé, MLOps est un ensemble de bonnes pratiques qui permettent de transformer les processus de machine learning en opérations efficaces et fiables.**

English answer:
MLOps, short for Machine Learning Operations, is a set of practices and tools that aim to streamline and automate the entire machine learning lifecycle. It encompasses all aspects of building, deploying, and maintaining machine learning models, from data collection and preparation to model training, deployment, monitoring, and retraining.

**Key Components of MLOps:**

* **Data Management:**  Managing data pipelines, ensuring data quality and consistency, and handling data versioning.
* **Model Development:** Building and training machine learning models using various algorithms and techniques.
* **Model Deployment:** Deploying models into production environments, ensuring scalability and performance.
* **Monitoring and Evaluation:** Tracking model performance, identifying issues, and triggering retraining as needed.
* **Version Control:** Maintaining versions of code, data, and models for reproducibility and tracking.
* **Infrastructure Automation:** Automating the deployment and management of ML infrastructure.
* **Collaboration and Communication:** Facilitating collaboration among data scientists, engineers, and other stakeholders.

**Benefits of MLOps:**

* **Faster Time to Market:** Streamlined workflows enable quicker deployment of ML models.
* **Improved Model Accuracy:**  Automated processes and consistent data ensure higher-quality models.
* **Enhanced Scalability and Reliability:**  Robust infrastructure and automation handle increasing workloads.
* **Increased Efficiency:**  Reduced manual effort and improved productivity.
* **Better Collaboration:**  Clear processes and communication facilitate teamwork.
* **Reduced Risk:**  Monitoring and automated retraining mitigate potential model drift.

**Tools and Technologies:**

* **Cloud Platforms:**  AWS, Azure, Google Cloud
* **Containerization:**  Docker, Kubernetes
* **Machine Learning Libraries:**  Scikit-learn, TensorFlow, PyTorch
* **Model Deployment Tools:**  Kubeflow, MLflow
* **Monitoring and Observability Tools:**  Prometheus, Grafana

**In essence, MLOps bridges the gap between data science and software engineering, enabling organizations to leverage the power of machine learning effectively and sustainably.**

Danish answer:
MLOps er en samling af praksisser og værktøjer, der hjælper med at automatisere og optimere maskinlæringslivscyklussen. Det handler om at bringe de bedste praksisser fra DevOps til maskinlæringsverdenen for at sikre, at maskinlæringsmodeller kan udvikles, implementeres og overvåges effektivt og pålideligt.

Her er nogle af de vigtigste elementer i MLOps:

* **Dataforberedelse og -kvalitet:** At sikre, at dataene bruges til at træne modeller er rene, konsistente og repræsentative for den virkelige verden.
* **Modeltræning og -evaluering:** Automatisering af processen med at træne og evaluere modeller for at finde den bedste præstation.
* **Modeludrulning og -overvågning:** Automatiseret udrulning af modeller til produktionsmiljøer og kontinuerlig overvågning for at sikre, at modellerne udfører som forventet.
* **Versionering og sporbarhed:** At holde styr på alle ændringer til modeller, data og kode for at kunne spore problemer og forbedringer.
* **Samarbejde og kommunikation:** At skabe en klar kommunikationslinje mellem datavidenskabsmænd, ingeniører og forretningsfolk for at sikre, at alle er på samme side.

MLOps er en vigtig del af at skabe succesfulde maskinlæringsapplikationer, da det hjælper med at sikre, at modellerne er robuste, pålidelige og kan håndtere ændringer i data og krav over tid.


Final answers:
Italian:
MLOps è un insieme di pratiche e tecnologie che consentono di sviluppare, distribuire e gestire i modelli di machine learning (ML) in modo efficiente e affidabile. In pratica, si tratta di applicare i principi DevOps al mondo del machine learning, automatizzando i processi e rendendo più facile la collaborazione tra data scientist, ingegneri e team aziendali.

Ecco alcuni aspetti chiave di MLOps:

* **Integrazione continua e consegna continua (CI/CD) per i modelli ML:**  automazione del processo di sviluppo, test e distribuzione dei modelli, rendendolo più veloce e affidabile.
* **Gestione del ciclo di vita del modello:**  monitoraggio delle prestazioni del modello nel tempo, identificazione delle aree di miglioramento e riaddestramento quando necessario.
* **Collaborazione:**  facilitazione della collaborazione tra team diversi, garantendo la condivisione di risorse, codice e dati.
* **Infrastruttura scalabile:**  fornitura di un'infrastruttura che possa gestire facilmente l'aumento del volume di dati e delle richieste di elaborazione.
* **Sicurezza e privacy:**  applicazione di pratiche di sicurezza e privacy per proteggere i dati e i modelli.

In sostanza, MLOps aiuta a portare il machine learning dal mondo della ricerca a quello della produzione, rendendolo un processo continuo e iterativo.


French:
**MLOps** est un ensemble de pratiques qui visent à automatiser et à industrialiser le cycle de vie complet du machine learning (ML), de la conception à la production. 

En d'autres termes, MLOps permet de mettre en place des processus robustes et efficaces pour développer, déployer et gérer des modèles ML à l'échelle.

**Voici quelques-uns des principaux aspects de MLOps :**

* **Automatisation:** MLOps automatise les tâches répétitives telles que la préparation des données, l'entraînement des modèles, le déploiement et la surveillance.
* **Collaboration:** MLOps facilite la collaboration entre les équipes de data science, d'ingénierie et d'opérations.
* **Gestion du cycle de vie:** MLOps couvre toutes les étapes du cycle de vie ML, de la conception à la production, en passant par le développement et la maintenance.
* **Surveillance et itérations:** MLOps permet de suivre les performances des modèles et de les mettre à jour régulièrement pour assurer leur exactitude et leur fiabilité.

**Les avantages de MLOps incluent :**

* Accélération du développement et du déploiement de modèles ML.
* Amélioration de la fiabilité et de la qualité des modèles.
* Réduction des coûts et des efforts associés à la gestion des modèles.
* Facilitation de la collaboration entre les équipes.

**En résumé, MLOps est un ensemble de bonnes pratiques qui permettent de transformer les processus de machine learning en opérations efficaces et fiables.**


English:
MLOps, short for Machine Learning Operations, is a set of practices and tools that aim to streamline and automate the entire machine learning lifecycle. It encompasses all aspects of building, deploying, and maintaining machine learning models, from data collection and preparation to model training, deployment, monitoring, and retraining.

**Key Components of MLOps:**

* **Data Management:**  Managing data pipelines, ensuring data quality and consistency, and handling data versioning.
* **Model Development:** Building and training machine learning models using various algorithms and techniques.
* **Model Deployment:** Deploying models into production environments, ensuring scalability and performance.
* **Monitoring and Evaluation:** Tracking model performance, identifying issues, and triggering retraining as needed.
* **Version Control:** Maintaining versions of code, data, and models for reproducibility and tracking.
* **Infrastructure Automation:** Automating the deployment and management of ML infrastructure.
* **Collaboration and Communication:** Facilitating collaboration among data scientists, engineers, and other stakeholders.

**Benefits of MLOps:**

* **Faster Time to Market:** Streamlined workflows enable quicker deployment of ML models.
* **Improved Model Accuracy:**  Automated processes and consistent data ensure higher-quality models.
* **Enhanced Scalability and Reliability:**  Robust infrastructure and automation handle increasing workloads.
* **Increased Efficiency:**  Reduced manual effort and improved productivity.
* **Better Collaboration:**  Clear processes and communication facilitate teamwork.
* **Reduced Risk:**  Monitoring and automated retraining mitigate potential model drift.

**Tools and Technologies:**

* **Cloud Platforms:**  AWS, Azure, Google Cloud
* **Containerization:**  Docker, Kubernetes
* **Machine Learning Libraries:**  Scikit-learn, TensorFlow, PyTorch
* **Model Deployment Tools:**  Kubeflow, MLflow
* **Monitoring and Observability Tools:**  Prometheus, Grafana

**In essence, MLOps bridges the gap between data science and software engineering, enabling organizations to leverage the power of machine learning effectively and sustainably.**


Danish:
MLOps er en samling af praksisser og værktøjer, der hjælper med at automatisere og optimere maskinlæringslivscyklussen. Det handler om at bringe de bedste praksisser fra DevOps til maskinlæringsverdenen for at sikre, at maskinlæringsmodeller kan udvikles, implementeres og overvåges effektivt og pålideligt.

Her er nogle af de vigtigste elementer i MLOps:

* **Dataforberedelse og -kvalitet:** At sikre, at dataene bruges til at træne modeller er rene, konsistente og repræsentative for den virkelige verden.
* **Modeltræning og -evaluering:** Automatisering af processen med at træne og evaluere modeller for at finde den bedste præstation.
* **Modeludrulning og -overvågning:** Automatiseret udrulning af modeller til produktionsmiljøer og kontinuerlig overvågning for at sikre, at modellerne udfører som forventet.
* **Versionering og sporbarhed:** At holde styr på alle ændringer til modeller, data og kode for at kunne spore problemer og forbedringer.
* **Samarbejde og kommunikation:** At skabe en klar kommunikationslinje mellem datavidenskabsmænd, ingeniører og forretningsfolk for at sikre, at alle er på samme side.

MLOps er en vigtig del af at skabe succesfulde maskinlæringsapplikationer, da det hjælper med at sikre, at modellerne er robuste, pålidelige og kan håndtere ændringer i data og krav over tid.
```