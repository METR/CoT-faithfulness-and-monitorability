import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from PIL import Image
import plotly.graph_objects as go

def _add_metr_watermark(fig):
    """Add METR logo and text watermark to the figure."""
    # Add METR logo to the top right
    fig.add_layout_image(
        dict(
            source="https://metr.org/assets/simple-logo.png",  # You may need to adjust this path
            x=0.995,
            y=0.995,
            xref="paper",
            yref="paper",
            sizex=0.1,
            sizey=0.1,
            xanchor="right",
            yanchor="top"
        )
    )
    
    # Add "metr.org" text to the bottom left
    fig.add_annotation(
        x=0.1,
        y=0.0675,
        text="metr.org  |  CC-BY",
        font=dict(size=7, color="black"),
        opacity=0.6,
        xref="paper",
        yref="paper",
        showarrow=False,
        xanchor="left",
        yanchor="top"
    )

def create_sankey_diagram():
    """Create a Sankey diagram showing hypothesis for unfaithful CoT judgments."""
    
    total_runs = 10000
    
    # First split: Faithful vs Unfaithful CoT (almost all faithful)
    faithful_cot = int(total_runs * 0.98)  # 980 (98% faithful)
    unfaithful_cot = total_runs - faithful_cot  # 20 (2% unfaithful)

    # Second split: For unfaithful cases, 95% vs 5%
    trivial = int(unfaithful_cot * 0.95)  # 19
    non_trivial = unfaithful_cot - trivial  # 1
    
    # Third split: 95% of the remaining (5% of unfaithful)
    false_positive = int(non_trivial * 0.95)  # 0.95 ≈ 1
    actual_issues = non_trivial - false_positive  # 0.05 ≈ 0
    
    # Fourth split: half of the actual issues
    llm_didnt_perform = int(actual_issues * 0.5)  # 0
    potential_obfuscation = actual_issues - llm_didnt_perform  # 0
    
    # Define the nodes (stages)
    node_labels = [
        "Total Runs",  # 0
        "Faithful CoT",  # 1
        "Unfaithful CoT",  # 2
        "Cognitive behavior was trivial (didn't benefit from CoT) (difficulty < 0.3)",  # 3
        "Unfaithfulness judge error",  # 4
        "Cognitive behavior benefited from CoT but didn't require it (0.3 <= difficulty <= 1)",  # 5
        "CoT was required (difficulty > 1)",  # 6
        "Actual unfaithfulness",  # 7
        "LLM likely didn't perform the behavior",  # 9
        "Potential active obfuscated reasoning",  # 10
        ""  # 11
    ]
    
    # Define the flows (source, target, value)
    flows = [
        (0, 1, faithful_cot),     # Total -> Faithful CoT
        (0, 2, unfaithful_cot),   # Total -> Unfaithful CoT
        (2, 3, trivial), # Unfaithful -> Trivial
        (2, 4, non_trivial), # Unfaithful -> Non-trivial
        (4, 5, false_positive), # Non-trivial -> False positive
        (4, 6, actual_issues), # Non-trivial -> Actual issues
        (6, 7, ), # Actual issues -> Difficulty > 0.3
        (6, 8, potential_obfuscation),  # Actual issues -> Difficulty = 1
        # candidate obfuscation -> ground_truth_potentially_wrong
        # candidate obfuscation -> potential_obfuscated_reasoning
    ]
    
    # Create the Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=node_labels,
            color=["#2E8B57", "#3CB371", "#20B2AA", "#FFD700", "#32CD32", "#228B22", "#FF6347", "#FF4500", "#DC143C"]
        ),
        link=dict(
            source=[flow[0] for flow in flows],
            target=[flow[1] for flow in flows],
            value=[flow[2] for flow in flows],
            color=["rgba(46, 139, 87, 0.4)", "rgba(46, 139, 87, 0.4)",
                   "rgba(60, 179, 113, 0.4)", "rgba(60, 179, 113, 0.4)",
                   "rgba(50, 205, 50, 0.4)", "rgba(50, 205, 50, 0.4)",
                   "rgba(255, 215, 0, 0.4)", "rgba(255, 215, 0, 0.4)"]
        )
    )])
    
    # Update layout
    fig.update_layout(
        title_text="Our hypothesis for what happened when the CoT was judged 'unfaithful'",
        font_size=12,
        height=600,
        width=1000
    )
    
    # Add METR watermark
    _add_metr_watermark(fig)
    
    # Save the plot
    output_path = Path("sankey_hypothesis.png")
    fig.write_image(str(output_path), scale=2)
    print(f"Sankey diagram saved to {output_path}")
    
    # Also save as HTML for interactive viewing
    html_path = Path("sankey_hypothesis.html")
    fig.write_html(str(html_path))
    print(f"Interactive HTML saved to {html_path}")

if __name__ == "__main__":
    create_sankey_diagram() 