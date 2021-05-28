# import spacy
# from spacy import displacy
# nlp = spacy.load('en_core_web_sm')

# from spacy.matcher import Matcher 
# from spacy.tokens import Span

# import networkx as nx
# from plotly.offline import plot
# import plotly.graph_objs as go

# def get_entities(sent):
#     ent1 = ""
#     ent2 = ""

#     prv_tok_dep = ""
#     prv_tok_text = ""

#     prefix = ""
#     modifier = ""
    
#     for tok in nlp(sent):
#         if tok.dep_ != "punct":
#             if tok.dep_ == "compound":
#                 prefix = tok.text
#                 if prv_tok_dep == "compound":
#                     prefix = prv_tok_text + " "+ tok.text
            
#             if tok.dep_.endswith("mod") == True:
#                 modifier = tok.text
#                 if prv_tok_dep == "compound":
#                     modifier = prv_tok_text + " "+ tok.text
            
#             if tok.dep_.find("subj") == True:
#                 ent1 = modifier +" "+ prefix + " "+ tok.text
#                 prefix = ""
#                 modifier = ""
#                 prv_tok_dep = ""
#                 prv_tok_text = ""      

#             if tok.dep_.find("obj") == True:
#                 ent2 = modifier +" "+ prefix +" "+ tok.text
                
#             prv_tok_dep = tok.dep_
#             prv_tok_text = tok.text

#     return (ent1.strip(), ent2.strip())

# def get_relation(sent):
#     doc = nlp(sent)

#     matcher = Matcher(nlp.vocab)

#     pattern = [{'DEP':'ROOT'}, 
#                 {'DEP':'prep','OP':"?"},
#                 {'DEP':'agent','OP':"?"},  
#                 {'POS':'ADJ','OP':"?"}] 

#     matcher.add("matching_1", None, pattern) 

#     matches = matcher(doc)
#     k = len(matches) - 1

#     span = doc[matches[k][1]:matches[k][2]] 

#     return(span.text)

# def extract_knowledge_graph(text_list):
#     G = nx.DiGraph()
#     for text in text_list:
#         head, tail = get_entities(text)
#         rel = get_relation(text)

#         if head and tail and rel:
#             G.add_nodes_from([head, tail])
#             G.add_edge(head, tail, relation=rel)
    
#     pos = nx.layout.spiral_layout(G)
#     for node in G.nodes:
#         G.nodes[node]['pos'] = list(pos[node])

#     traceRecode = []
#     node_trace = go.Scatter(x=[], y=[], hovertext=[], text=[], mode='markers+text', textposition="bottom center",
#                             hoverinfo="text", marker={'size': 15, 'color': 'Blue'})

#     for node in G.nodes():
#         x, y = G.nodes[node]['pos']
#         hovertext = node
#         node_trace['x'] += tuple([x])
#         node_trace['y'] += tuple([y])
#         node_trace['hovertext'] += tuple([hovertext])
        
#     traceRecode.append(node_trace)
    
#     for edge in G.edges:
#         x0, y0 = G.nodes[edge[0]]['pos']
#         x1, y1 = G.nodes[edge[1]]['pos']
#         trace = go.Scatter(x=tuple([x0, x1, None]), y=tuple([y0, y1, None]),
#                         mode='lines',
#                         line=dict(width=0.5, color='#888'),
#                         line_shape='spline',
#                         opacity=1)
#         traceRecode.append(trace)

#     middle_hover_trace = go.Scatter(x=[], y=[], hovertext=[], mode='markers', hoverinfo="text",marker={'size': 15, 'color': 'LightSkyBlue'},opacity=0)
#     for node1, node2, data in G.edges(data=True):
#         x0, y0 = G.nodes[node1]['pos']
#         x1, y1 = G.nodes[node2]['pos']
#         hovertext = data['relation']
#         middle_hover_trace['x'] += tuple([(x0 + x1) / 2])
#         middle_hover_trace['y'] += tuple([(y0 + y1) / 2])
#         middle_hover_trace['hovertext'] += tuple([hovertext])
#     traceRecode.append(middle_hover_trace)
    
#     fig = {
#     "data": traceRecode,
#     "layout": go.Layout(title='Interactive Transaction Visualization', showlegend=False, hovermode='closest',
#                         margin={'b': 40, 'l': 40, 'r': 40, 't': 40},
#                         xaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False},
#                         yaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False},
#                         height=600,
#                         clickmode='event+select',
#                         annotations=[
#                             dict(
#                                 ax=(G.nodes[edge[0]]['pos'][0] + G.nodes[edge[1]]['pos'][0]) / 2,
#                                 ay=(G.nodes[edge[0]]['pos'][1] + G.nodes[edge[1]]['pos'][1]) / 2, axref='x', ayref='y',
#                                 x=(G.nodes[edge[1]]['pos'][0] * 3 + G.nodes[edge[0]]['pos'][0]) / 4,
#                                 y=(G.nodes[edge[1]]['pos'][1] * 3 + G.nodes[edge[0]]['pos'][1]) / 4, xref='x', yref='y',
#                                 showarrow=True,
#                                 arrowhead=3,
#                                 arrowsize=2,
#                                 arrowwidth=1,
#                                 opacity=1
#                             ) for edge in G.edges]
#                         )}

#     plot_div = plot(fig,
#                     output_type='div', 
#                     include_plotlyjs=False,
#                     show_link=False, 
#                     link_text="")

#     return plot_div



# # https://towardsdatascience.com/python-interactive-network-visualization-using-networkx-plotly-and-dash-e44749161ed7
# # https://plotly.com/python/network-graphs/