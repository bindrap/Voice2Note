from ollama import Client
import os
from config import Config


class NoteGenerator:
    """Generates structured notes from transcripts using Ollama"""

    def __init__(self):
        self.client = Client(
            host=Config.OLLAMA_HOST,
            headers={'Authorization': f'Bearer {Config.OLLAMA_API_KEY}'}
        )
        self.model = Config.OLLAMA_MODEL

    def generate_notes(self, transcript_text, metadata=None):
        """
        Generate structured markdown notes from transcript

        Args:
            transcript_text: The transcript text
            metadata: Optional dict with video metadata (title, channel, etc.)

        Returns:
            str: Generated markdown notes
        """
        # Build prompt with metadata if available
        prompt = self._build_prompt(transcript_text, metadata)

        print("Generating notes with Ollama...")
        print(f"Model: {self.model}")
        print(f"Transcript length: {len(transcript_text)} characters")

        try:
            # Call Ollama API
            notes = ""
            messages = [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]

            # Stream response
            for part in self.client.chat(self.model, messages=messages, stream=True):
                content = part.get('message', {}).get('content', '')
                notes += content
                print('.', end='', flush=True)

            print("\n✓ Notes generated successfully!")
            return notes

        except Exception as e:
            raise Exception(f"Failed to generate notes: {str(e)}")

    def _build_prompt(self, transcript_text, metadata):
        """Build the prompt for note generation"""

        # Base prompt
        prompt = """You are an expert note-taker creating comprehensive, detailed, and well-structured notes from video transcripts.

Your task is to convert the following transcript into exceptional markdown notes that capture ALL the information presented.

IMPORTANT GUIDELINES:
- DO NOT summarize or skip content - capture ALL details, explanations, and information
- DO NOT remove examples, stories, or contextual information
- DO NOT condense multiple concepts into single points
- Include ALL technical details, specifications, and explanations
- Preserve the flow and progression of ideas from the original content
- If the speaker explains something in depth, your notes should reflect that depth
- When in doubt, include MORE detail rather than less

Your notes should be:
- Well-organized with clear headings and subheadings
- Comprehensive and detailed (not abbreviated or summarized)
- Easy to scan and navigate
- Properly formatted in markdown

Please include:
1. A brief overview at the top (2-3 sentences)
2. Main concepts organized by topic (use ## for main sections, ### for subsections)
3. Detailed bullet points that capture ALL information (not just highlights)
4. Important terms, names, definitions, or concepts in **bold**
5. Complete step-by-step instructions or processes (if applicable) as numbered lists
6. All examples, use cases, and practical applications mentioned
7. Code examples in code blocks with full context (if applicable)
8. Important quotes in blockquotes
9. A "Key Takeaways" section at the end with 5-10 comprehensive points
10. A "Additional Details" section if there's extra context worth preserving

Remember: Your goal is to create notes so comprehensive that someone could understand the full content WITHOUT watching the video. Don't leave out important information!

"""

        # Add metadata if available
        if metadata:
            prompt += "## Video Information:\n"
            if metadata.get('title'):
                prompt += f"- **Title**: {metadata['title']}\n"
            if metadata.get('channel'):
                prompt += f"- **Creator**: {metadata['channel']}\n"
            if metadata.get('duration'):
                minutes = metadata['duration'] // 60
                prompt += f"- **Duration**: {minutes} minutes\n"
            if metadata.get('url'):
                prompt += f"- **Source**: {metadata['url']}\n"
            prompt += "\n"

        # Add transcript
        prompt += f"""## Transcript:

{transcript_text}

---

Now, create well-structured markdown notes from this transcript. Start with a clear title (# heading) based on the content:
"""

        return prompt

    def generate_notes_chunked(self, transcript_chunks, metadata=None):
        """
        Generate notes from multiple transcript chunks

        Args:
            transcript_chunks: List of transcript text chunks
            metadata: Optional video metadata

        Returns:
            str: Combined markdown notes
        """
        if len(transcript_chunks) == 1:
            return self.generate_notes(transcript_chunks[0], metadata)

        print(f"Generating notes from {len(transcript_chunks)} chunks...")

        all_notes = []

        for i, chunk in enumerate(transcript_chunks, 1):
            print(f"\nProcessing chunk {i}/{len(transcript_chunks)}...")

            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata['chunk_info'] = f"Part {i} of {len(transcript_chunks)}"

            notes = self.generate_notes(chunk, chunk_metadata)
            all_notes.append(notes)

        # Combine notes with separators
        combined_notes = "\n\n---\n\n".join(all_notes)

        # Add a summary note at the top
        if metadata and metadata.get('title'):
            title = metadata['title']
            header = f"# {title}\n\n*These notes were generated from a long video and are split into {len(transcript_chunks)} parts.*\n\n"
            combined_notes = header + combined_notes

        return combined_notes

    def improve_notes(self, existing_notes, feedback):
        """
        Improve existing notes based on user feedback

        Args:
            existing_notes: Current markdown notes
            feedback: User feedback for improvement

        Returns:
            str: Improved markdown notes
        """
        prompt = f"""You are helping improve existing notes based on user feedback.

## Current Notes:
{existing_notes}

## User Feedback:
{feedback}

Please update the notes according to the feedback while maintaining the markdown structure and improving clarity. Return only the improved notes:
"""

        try:
            notes = ""
            messages = [{'role': 'user', 'content': prompt}]

            for part in self.client.chat(self.model, messages=messages, stream=True):
                content = part.get('message', {}).get('content', '')
                notes += content

            return notes

        except Exception as e:
            raise Exception(f"Failed to improve notes: {str(e)}")
