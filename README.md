# conversational-story-generation
Our project combines state-of-the-art NLP and computer vision techniques to generate coherent stories. By fine-tuning GPT-3.5 on the STORIUM [1] dataset and using DALL-E for text-to-image generation, we provide a platform that can be used to generate high-quality stories in real time along with the visual illustration

## Dataset
- Our dataset is a collection of stories sourced from Storium used to train both our story generation model and storyline guidance model.
- It consists of 5743 stories, including a large corpus of 25,092 scenes, containing a diverse range of stories comprising a wide range of narrative scenarios, characters and plotlines.
- Within the Storium dataset, each story is structured into scenes, each scene representing a discrete unit of the narrative

## How it works
- **Generation**: Fine-tuned GPT-3.5 makes storyline (by giving character, event, and place) and guides non-fine-tuned GPT-3.5.
- **Guidance**: Non-fine-tuned GPT-3.5 generates the paragraph based on what it gets from the fine-tuned GPT-3.5
- **Visualization**: DALL-E gets the generated paragraph character, event, and place to generate the corresponding image
  ![image](https://github.com/MohtashimButt/conversational-story-generation/assets/87702903/27890423-c140-453e-8035-07ce6822244b)

## MCQA Approach in GPT-3.5 fine-tuning
The Storium dataset is prepared in a way that for every revert, it contains a short description along with the character involved in it, and the place in which it is occurring. By taking advantage of Storium's nature, we extracted the key details (event description, characters, and places) and fine-tuned GPT-3.5 in a Q/A way (known as the MCQA approach [2]) to maintain coherence in the generated paragraph. 
![image](https://github.com/MohtashimButt/conversational-story-generation/assets/87702903/9b1e8870-26fc-40e9-b86e-a0b524c3225f)
The generation would occur paragraph-by-paragraph

## Deployment
The project has been deployed at: https://gen-ai-woad.vercel.app/

## A few screenshots
![image](https://github.com/MohtashimButt/conversational-story-generation/assets/87702903/558de3d3-5433-4934-bac7-cc289e9dbdbc)


## References
[1] Akoury, N., Wang, S., Whiting, J., Hood, S., Peng, N., & Iyyer, M. (2020). Storium: A dataset and evaluation platform for machine-in-the-loop story generation. arXiv preprint arXiv:2010.01717.
[2] Kim, Juntae, et al. "A Multi-Modal Story Generation Framework with AI-Driven Storyline Guidance." Electronics 12.6 (2023): 1289.
