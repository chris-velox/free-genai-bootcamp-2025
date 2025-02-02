# Requirements

## Business Requirements

### Business Goals and Objectives

The company currently hosts in-person German language teaching classes and private tutoring. The purpose of this project is to build a system to augment those sessions with on-demand, online learning tools. The company is currently calling this system "SprachPortal".

The company wants to build a language teaching system for their students that provides interactive exercises to enhance student learning. The company wants to build a system they control because of student privacy and learning material copyright concerns. Investment in a dedicated solution will allow the company to control the teaching methods they have developed within their system.

The company wants to tightly control costs, so is looking for a cost-effective solution that will support their current student base.

## Functional Requirements

### Teaching Functions

SprachPortal shall provide the following language teach functions within or through the system:

#### Sentence Constructor

The Sentence Constructor will generate sentences at the appropriate level for the student to translate. The student can select the topic the sentences will cover, the translation direction (English to German, or German to English) and the number of sentences for the exercise.

#### Visual Vocabulary Flashcards

The Visual Vocabulary Flashcards will generate level-appropriate vocabulary flashcards to quiz students on vocabulary. The flashcards will support:
- Shown English word, student provides German translation
- Shown German word, student provides English translation
- Picture (nouns), student provides German translation

At the basic levels, answers will be multiple choice. As students gain proficiency, they will have to type the answer for the system to check. At the advanced levels, the system will support multiple possible answers, if appropriate, and recommend the best answer if not provided by the student.

#### Writing Practice

The Writing Practice activity will allow the student to construct their own writing in German and the system will check the sentence for spelling and grammar correctness, and the literalism of the sentence. Ideally, the system will also recognize typical English language idioms and colloquialisms and provide suggestions for equivalent German phrases.

#### Listen to Learn

The Listen to Learn activity will provide text-to-speech capabilities to speak words in German and have the students transcribe the words or provide an English language translation. As the student progresses in proficiency, the spoken text will grow to sentences of increasing complexity.

#### Speak to Learn

The Speak to Learn activity will allow students to speak into a microphone and have the system rate their ability to properly pronounce the words. The system will make corrections and recommendations on correct pronunciation.

#### Graphic Novel Immersion Reading

The Graphic Novel Immersion Reading will present the student with pictures and German text that tell a story. The system will ask the students questions about each page of the story and summary questions at the end.

#### Text Adventure Immersion Game

The Text Adventure Immersion Game will generate a German "choose your own adventure" story at an appropriate level for the student. Student level will determine the length of the story and complexity of the sentences.

### Student-Related Functions

#### Student Registration

The Student Registration system will capture appropriate student information. This information will be kept private and secure. Information collected:
- Username
- Name
- Age
- Email

#### Student Activity Tracking

Student Activity Tracking will track the students' proficiency with the language exercises.

Student Activity Tracking will also display any activity assignments made by teachers to the students and the expected dates the activities should be completed.

### Teacher-Related Functions

#### Teacher Registration

The Teacher Registration system will capture appropriate teacher information. This information will be kept private and secure. Information collected:
- Username
- Name
- Email

#### Student Assignments

Teachers will be able to provide activity recommendations and assignments to students, and see if the students have completed them.

#### Student Progress

Teachers will be able to view the progress of students through all the activities they have completed, how long it takes students to complete each activity (both time to start an activity and duraction of active work in the activity).

## Non-Functional Requirements

### Performance and Capacity

### Availability

### Security and Privacy

