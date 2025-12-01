"""
This file generates summaries, questions, and hints WITHOUT using AI.
It uses simple text processing rules to create learning content.
"""

import re


def extract_keywords(text, num_keywords=5):
    """
    Extract important words from text (simple approach).
    
    Args:
        text: The text to analyze
        num_keywords: How many keywords to extract
        
    Returns:
        List of keywords
    """
    # Remove common words (stop words)
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
        'these', 'those', 'it', 'its', 'they', 'them', 'their'
    }
    
    # Convert to lowercase and split into words
    words = re.findall(r'\b[a-z]{4,}\b', text.lower())
    
    # Filter out stop words
    keywords = [w for w in words if w not in stop_words]
    
    # Count frequency
    word_freq = {}
    for word in keywords:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and get top keywords
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    
    return [word for word, freq in sorted_words[:num_keywords]]


def create_summary(text, max_sentences=4):
    """
    Create a simple summary by extracting the first few sentences.
    
    Args:
        text: The full text
        max_sentences: How many sentences to include
        
    Returns:
        A summary string
    """
    # Split into sentences (simple approach)
    sentences = re.split(r'[.!?]+', text)
    
    # Clean up sentences
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    
    # Take first few sentences
    summary_sentences = sentences[:max_sentences]
    
    # Join them back
    summary = '. '.join(summary_sentences)
    
    if summary and not summary.endswith('.'):
        summary += '.'
    
    return summary if summary else "This section covers important concepts related to the topic."


def generate_questions(topic_title, topic_content, keywords):
    """
    Generate simple questions based on the content.
    
    Args:
        topic_title: The title of the topic
        topic_content: The text content
        keywords: List of important keywords
        
    Returns:
        List of question dictionaries
    """
    questions = []
    
    # Question 1: About the main topic
    questions.append({
        "question": f"What is the main focus of '{topic_title}'?",
        "answer": f"The main focus is on {topic_title.lower()} and its key concepts including {', '.join(keywords[:3]) if keywords else 'various aspects'}."
    })
    
    # Question 2: About key concepts (using keywords)
    if len(keywords) >= 2:
        questions.append({
            "question": f"Explain the relationship between {keywords[0]} and {keywords[1]} in this topic.",
            "answer": f"{keywords[0].capitalize()} and {keywords[1]} are related concepts in {topic_title.lower()}."
        })
    else:
        questions.append({
            "question": f"What are the key concepts discussed in {topic_title}?",
            "answer": f"The key concepts include the fundamental ideas and principles of {topic_title.lower()}."
        })
    
    # Question 3: Application question
    if keywords:
        questions.append({
            "question": f"How would you apply the concept of {keywords[0]} in a real-world scenario?",
            "answer": f"{keywords[0].capitalize()} can be applied in various practical situations related to {topic_title.lower()}."
        })
    else:
        questions.append({
            "question": f"Why is understanding {topic_title} important?",
            "answer": f"Understanding {topic_title.lower()} is important for grasping related concepts and applications."
        })
    
    return questions


def generate_hints(topic_content, keywords):
    """
    Generate hints based on the content.
    
    Args:
        topic_content: The text content
        keywords: List of important keywords
        
    Returns:
        List of hint strings
    """
    hints = []
    
    # Hint 1: Think about keywords
    if keywords:
        hints.append(f"Think about these key terms: {', '.join(keywords[:3])}.")
    else:
        hints.append("Think about the main concepts discussed in the text.")
    
    # Hint 2: General hint
    hints.append("Review the summary and look for the most important ideas mentioned.")
    
    return hints


def generate_level_content(topic_title, topic_content):
    """
    Generate complete level content WITHOUT using AI.
    Uses simple text processing to create summaries, questions, and hints.
    
    Args:
        topic_title: The name of the topic
        topic_content: The actual text content of the topic
        
    Returns:
        A dictionary with summary, questions, hints, and a keyword
    """
    try:
        # Extract keywords from the content
        keywords = extract_keywords(topic_content)
        
        # Create a summary
        summary = create_summary(topic_content)
        
        # Generate questions
        questions = generate_questions(topic_title, topic_content, keywords)
        
        # Generate hints
        hints = generate_hints(topic_content, keywords)
        
        # Pick the most important keyword
        main_keyword = keywords[0] if keywords else topic_title.split()[0]
        
        return {
            "summary": summary,
            "questions": questions,
            "hints": hints,
            "keyword": main_keyword.upper()
        }
        
    except Exception as e:
        print(f"Error generating content: {e}")
        
        # Return fallback content if processing fails
        return {
            "summary": f"This level covers the topic of {topic_title}. Study the key concepts and their applications to better understand this subject.",
            "questions": [
                {
                    "question": f"What is the main idea of {topic_title}?",
                    "answer": f"The main concepts discussed in {topic_title.lower()}"
                },
                {
                    "question": f"Why is {topic_title} important?",
                    "answer": f"Its significance and applications in the field"
                },
                {
                    "question": f"How does {topic_title} relate to other concepts?",
                    "answer": f"Connections to related topics and ideas"
                }
            ],
            "hints": [
                "Think about the key concepts mentioned in the summary.",
                "Consider the practical applications discussed."
            ],
            "keyword": topic_title.split()[0].upper()
        }