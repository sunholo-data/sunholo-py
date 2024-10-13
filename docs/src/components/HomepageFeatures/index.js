import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';
import IdealImage from '@theme/IdealImage';  // Import IdealImage component
import multivacDeployments from '@site/static/img/multivac-deployments.png'; // Use ES module import
import multivacVenn from '@site/static/img/multivac-venn.png';
import multivacArch from '@site/static/img/multivac-arch.png';

const FeatureList = [
  {
    title: 'GenAI Experimentation',
    Img: multivacDeployments, 
    description: (
      <>
        Update GenAI service dependencies via a config file. 
        Launch new configurations in minutes, leveraging common resources such
        as VPC, IAM, analytics, prompt libraries, model evals and database instances.
      </>
    ),
  },
  {
    title: 'GenAI in the Cloud',
    Img: multivacVenn,
    description: (
      <>
        The Sunholo Multivac system offers an abstraction between your GenAI application
        and the Cloud.  Deploy applications running Langchain/LlamaIndex or your
        custom code to cloud services such as vectorstores and serverless compute.
      </>
    ),
  },
  {
    title: 'Flexible and Scalable',
    Img: multivacArch,
    description: (
      <>
        Develop Locally and deploy Globally by publishing to the Multivac SaaS, or your own Cloud PaaS.
        Event based serverless backend allows flexiblity to use bundled UIs such as webapps or chatbots, or
        hook into APIs to create your own user experience.
      </>
    ),
  },
];

function Feature({Img, title, description}) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
      <IdealImage img={Img} className={styles.featureImg} alt={title} />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
