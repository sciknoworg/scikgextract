from typing import Dict, List

import evaluate
from transformers import AutoTokenizer, PreTrainedTokenizer
from sentence_transformers import SentenceTransformer, util

import numpy as np
from scipy.optimize import linear_sum_assignment


def rouge_score(references: list, predictions: list) -> dict:
    """
    Calculate the ROUGE scores between the reference output and the predicted output
    Args:
        references (list): The list of reference outputs
        predictions (list): The list of predicted outputs
    Returns:
        dict: The ROUGE score
    """
    rouge = evaluate.load("rouge")
    return rouge.compute(predictions=predictions, references=references)


def bleu_score(references: list, predictions: list) -> dict:
    """
    Calculate the BLEU scores between the reference output and the predicted output
    Args:
        references (list): The list of reference outputs
        predictions (list): The list of predicted outputs
    Returns:
        dict: The BLEU score
    """
    bleu = evaluate.load("bleu")
    return bleu.compute(predictions=predictions, references=references)


def split_into_chunks(text: str, tokenizer: PreTrainedTokenizer, max_length: int = 512) -> list:
    """
    Split the input text into chunks based on the tokenizer and max length
    Args:
        text (str): The input text to be split
        tokenizer (PreTrainedTokenizer): The tokenizer to be used for splitting
        max_length (int): The maximum length of each chunk
    Returns:
        list: The list of text chunks
    """
    tokens = tokenizer.encode(text, add_special_tokens=False)
    chunks = [
        tokens[i : i + max_length - 4] for i in range(0, len(tokens), max_length - 4)
    ]
    return [tokenizer.decode(chunk, skip_special_tokens=False) for chunk in chunks]


def bert_score(references: list, predictions: list, embedding_model: str, embedding_model_revision: str, max_length: int = 256) -> dict:
    """
    Calculate the BERT scores between the reference output and the predicted output
    Args:
        references (list): The list of reference outputs
        predictions (list): The list of predicted outputs
        embedding_model (str): The name of the embedding model to be used
        embedding_model_revision (str): The revision of the embedding model to be used
        max_length (int): The maximum length of each chunk
    Returns:
        dict: The BERT score
    """
    # Loading the BERT score and Embedding model from HuggingFace
    bertscore = evaluate.load("bertscore")
    tokenizer = AutoTokenizer.from_pretrained(
        embedding_model, revision=embedding_model_revision  # nosec B615
    )

    # Intializing dictionary for storing intermediate scores
    scores: Dict[str, List[float]] = {"precision": [], "recall": [], "f1": []}

    # Iterating each reference and prediction pair
    for pred, ref in zip(predictions, references):
        pred_chunks = split_into_chunks(pred, tokenizer, max_length)
        ref_chunks = split_into_chunks(ref, tokenizer, max_length)

        # Calculating bert score for each chunk separately
        for p_chunk, r_chunk in zip(pred_chunks, ref_chunks):
            result = bertscore.compute(
                predictions=[p_chunk],
                references=[r_chunk],
                model_type=embedding_model,
                lang="en"
            )
            scores["precision"].append(result["precision"][0])
            scores["recall"].append(result["recall"][0])
            scores["f1"].append(result["f1"][0])

    # Aggregating the scores - average across chunks
    scores_avg = {
        "precision": sum(scores["precision"]) / len(scores["precision"]),
        "recall": sum(scores["recall"]) / len(scores["recall"]),
        "f1": sum(scores["f1"]) / len(scores["f1"]),
    }
    return scores_avg

def cosine_similarity_score(references: list, predictions: list, embedding_model: str, max_length: int = 512) -> dict:
    """
    Calculate the Cosine Similarity scores between the reference output and the predicted output
    Args:
        references (list): The list of reference outputs
        predictions (list): The list of predicted outputs
        embedding_model (str): The name of the embedding model to be used
        max_length (int): The maximum length of each chunk
    Returns:
        dict: The Cosine Similarity score
    """
    # Loading the Embedding model from Sentence Transformers
    model = SentenceTransformer(embedding_model)

    # Intializing list for storing similarity scores
    similarity_scores: List[float] = []

    # Iterating each reference and prediction pair
    for pred, ref in zip(predictions, references):
        pred_chunks = split_into_chunks(pred, model.tokenizer, max_length)
        ref_chunks = split_into_chunks(ref, model.tokenizer, max_length)

        # Calculating cosine similarity for each chunk separately
        for p_chunk, r_chunk in zip(pred_chunks, ref_chunks):
            emb1 = model.encode(p_chunk, convert_to_tensor=True)
            emb2 = model.encode(r_chunk, convert_to_tensor=True)
            cosine_score = util.cos_sim(emb1, emb2).item()
            similarity_scores.append(cosine_score)

    # Aggregating the scores - average across chunks
    average_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0
    return average_similarity

def hungarian_similarity(sent1: str, sent2: str, embedding_model: str = "allenai/scibert_scivocab_uncased") -> float:
    
    # Load the embedding model
    model = SentenceTransformer(embedding_model)
    
    # Tokenize sentences
    tokens1 = sent1.split()
    tokens2 = sent2.split()
    
    # Get token embeddings
    emb1 = model.encode(tokens1)
    emb2 = model.encode(tokens2)
    
    # Build a cost matrix using cosine distance
    cost_matrix = np.zeros((len(tokens1), len(tokens2)))
    for i in range(len(tokens1)):
        for j in range(len(tokens2)):
            v1 = emb1[i]
            v2 = emb2[j]
            # Cosine distance = 1 - cosine similarity
            cost_matrix[i, j] = 1 - np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    
    # Solve the assignment problem (minimize total cost)
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    
    # Compute average similarity (convert distance back to similarity)
    total_similarity = 0
    for r, c in zip(row_ind, col_ind):
        total_similarity += 1 - cost_matrix[r, c]
    
    # Normalize by max number of tokens
    score = total_similarity / max(len(tokens1), len(tokens2))
    return score