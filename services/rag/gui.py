import gradio as gr
from pipeline import query_RAG


def chat(message, history):
    answer, sources = query_RAG(message, history)
    history.append([message, answer])
    return "", history, sources


with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# WSU Campus Assistant")
    gr.Markdown("Ask me anything about WSU events, clubs, and campus life")

    chatbot = gr.Chatbot(height=500)

    with gr.Row():
        msg = gr.Textbox(placeholder="Ask me anything about WSU...", show_label=False, scale=4)
        send_btn = gr.Button("Send", variant="primary", scale=1)
        clear_btn = gr.Button("Clear", scale=1)

    with gr.Accordion("Retrieved Documents", open=False):
        sources_box = gr.Textbox(label="Top 5 relevant sources", lines=8, interactive=False)

    gr.Examples(
        examples=[
            "What free events are happening this week?",
            "What clubs does WSU have?",
            "When is the last day to withdraw from classes?",
            "What is the Engineering Open House?",
        ],
        inputs=msg
    )

    send_btn.click(chat, [msg, chatbot], [msg, chatbot, sources_box])
    msg.submit(chat, [msg, chatbot], [msg, chatbot, sources_box])
    clear_btn.click(lambda: ([], ""), None, [chatbot, sources_box])


demo.launch(share=True)
