# conversational-story-generation

The primary goal of this project is to develop a system that provides a multimodal storytelling experience.

## Goal
The primary goal of our project is to develop a system that provides a multimodal storytelling experience. We envision equipping our model with the following general high-level functionality:

- Take initial user input for the storyline
    - This seed serves as the starting point for the generation of the story.
    - It could potentially consist of Character, Place, and Event (inspired by Kim et al.). Alternatively, it could have a set of phrases forming the outline (inspired by Rashkin et al.)
- Generate paragraphs
    - The generation would occur paragraph-by-paragraph
    - A set of paragraphs (threshold to be decided during actual implementation) would form a long story
    - The paragraphs should logically follow each other in terms of events and characters.
- Visual images
    - A scene/set of scenes should be depicted with a set of images (sort of a comic-book fashion)
    - These images should align with the storyline
- Sound effects (Extra feature)
    - A scene/set of scenes should have associated sound effects (inspired by Bae et al.)
    - These would basically be background sound which is story context-based audio without any linguistic information
    - This could be based on the images or the text related to the scene(s), whichever is more feasible

## References
Kim, Juntae, et al. "A Multi-Modal Story Generation Framework with AI-Driven Storyline Guidance." Electronics 12.6 (2023): 1289.
