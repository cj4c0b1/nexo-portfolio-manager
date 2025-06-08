import plotly.graph_objects as go
import plotly.express as px

# Define the data
data = {
  "nodes": [
    {"id": "main", "label": "Main App", "file": "(main.py)", "description": "Streamlit entry", "layer": "ui", "x": 400, "y": 50},
    {"id": "dashboard", "label": "Dashboard UI", "file": "(dashboard.py)", "description": "User interface", "layer": "ui", "x": 200, "y": 150},
    {"id": "portfolio", "label": "Portfolio Mgr", "file": "(portfolio.py)", "description": "Portfolio ops", "layer": "business", "x": 400, "y": 150},
    {"id": "rebalancer", "label": "Rebalancer", "file": "(rebalancer.py)", "description": "Rebalance logic", "layer": "business", "x": 600, "y": 150},
    {"id": "database", "label": "Database Mgr", "file": "(database.py)", "description": "SQLite ops", "layer": "data", "x": 200, "y": 250},
    {"id": "market_data", "label": "Market Data", "file": "(market_data.py)", "description": "Price feeds", "layer": "data", "x": 400, "y": 250},
    {"id": "nexo_client", "label": "Nexo API", "file": "(nexo_client.py)", "description": "API integration", "layer": "data", "x": 600, "y": 250},
    {"id": "config", "label": "Config", "file": "(settings.py)", "description": "App settings", "layer": "foundation", "x": 200, "y": 350},
    {"id": "models", "label": "Data Models", "file": "(models.py)", "description": "Data structures", "layer": "foundation", "x": 400, "y": 350},
    {"id": "helpers", "label": "Utilities", "file": "(helpers.py)", "description": "Helper funcs", "layer": "foundation", "x": 600, "y": 350}
  ],
  "connections": [
    {"from": "main", "to": "dashboard"},
    {"from": "main", "to": "portfolio"},
    {"from": "portfolio", "to": "rebalancer"},
    {"from": "dashboard", "to": "portfolio"},
    {"from": "portfolio", "to": "database"},
    {"from": "portfolio", "to": "market_data"},
    {"from": "rebalancer", "to": "nexo_client"},
    {"from": "rebalancer", "to": "market_data"},
    {"from": "database", "to": "models"},
    {"from": "market_data", "to": "config"},
    {"from": "nexo_client", "to": "config"},
    {"from": "dashboard", "to": "helpers"}
  ]
}

# Create node lookup dictionary
node_dict = {node['id']: node for node in data['nodes']}

# Define colors for layers
layer_colors = {
    'ui': '#1FB8CD',        # Blue (Strong cyan)
    'business': '#ECEBD5',  # Green (Light green) 
    'data': '#FFC185',      # Orange (Light orange)
    'foundation': '#5D878F' # Gray (Cyan - close to gray)
}

# Create figure
fig = go.Figure()

# Add connection lines first (so they appear behind nodes)
for connection in data['connections']:
    from_node = node_dict[connection['from']]
    to_node = node_dict[connection['to']]
    
    fig.add_trace(go.Scatter(
        x=[from_node['x'], to_node['x']],
        y=[from_node['y'], to_node['y']],
        mode='lines',
        line=dict(color='#CCCCCC', width=2),
        hoverinfo='skip',
        showlegend=False
    ))

# Add rectangular nodes using shapes and annotations
box_width = 80
box_height = 40

for node in data['nodes']:
    color = layer_colors[node['layer']]
    
    # Add rectangle shape
    fig.add_shape(
        type="rect",
        x0=node['x'] - box_width/2,
        y0=node['y'] - box_height/2,
        x1=node['x'] + box_width/2,
        y1=node['y'] + box_height/2,
        fillcolor=color,
        line=dict(color='white', width=2)
    )
    
    # Add text annotation
    fig.add_annotation(
        x=node['x'],
        y=node['y'] + 5,
        text=f"<b>{node['label']}</b><br>{node['file']}<br><i>{node['description']}</i>",
        showarrow=False,
        font=dict(size=9, color='black'),
        align='center'
    )

# Add invisible traces for legend
for layer_name, color in layer_colors.items():
    fig.add_trace(go.Scatter(
        x=[None],
        y=[None],
        mode='markers',
        marker=dict(size=15, color=color, symbol='square'),
        name=layer_name.capitalize(),
        showlegend=True
    ))

# Update layout
fig.update_layout(
    title='Nexo Portfolio Manager Architecture',
    showlegend=True,
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=1.05,
        xanchor='center',
        x=0.5
    ),
    plot_bgcolor='white'
)

# Update axes
fig.update_xaxes(
    showgrid=False,
    zeroline=False,
    showticklabels=False,
    range=[100, 700]
)

fig.update_yaxes(
    showgrid=False,
    zeroline=False,
    showticklabels=False,
    range=[0, 400],
    autorange='reversed'  # Reverse y-axis so main is at top
)

# Save the chart
fig.write_image('nexo_architecture_chart.png', width=800, height=600)