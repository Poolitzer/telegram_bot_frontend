This is a short manual about how to add questions/answers to the graph.

The design approach is a simple graph structure. Each node represents a question, each edge a list of possible answers. The last answers will point to an non existing node, which will be expected by the logic and treated as the end of the QA session.

Based on that, we have multiple possibilities on how to set up a question and answer flow. The most basic one is asking a question (creating the node), giving Yes or No as the possible answers, both going to the next question.
```xml
<graph defaultedgetype="directed">
    <nodes>
      <node id="0" label="NORMAL_QUESTION"/>
    </nodes>
    <edges>
      <edge id="0" source="0" target="1" label="NORMAL_ANSWER"/>
    </edges>
</graph>
```
More complicated would be splitting up the answers. Given question A (Are you male/female), Answer a (male) and b (female), we can follow up ask the female question B (Are you pregnant), then asking her question C (do you smoke). Male users are directly asked C. So node A has edges a and b, a leading to node C, b leading to node B, then the edge leads over to C.
```xml
<graph defaultedgetype="directed">
    <nodes>
      <node id="A" label="GENDER_QUESTION"/>
      <!--Makes no sense to ask a male if he's pregnant-->
      <node id="B" label="PREGNANT_QUESTION"/>
      <node id="C" label="SMOKE_QUESTION"/>
    </nodes>
    <edges>
      <edge id="a" source="A" target="C" label="MALE_ANSWER"/>
      <edge id="b" source="A" target="B" label="FEMALE_ANSWER"/>
      <edge id="c" source="B" target="C" label="PREGNANCY_ANSWER"/>
    </edges>
</graph>
```
We can even ask multiple choice questions. Then we can't split the answers, they must be on one edge!
```xml
<graph defaultedgetype="directed">
    <nodes>
      <node id="0" label="MULTI_QUESTION">
        <attvalues>
          <attvalue for="0" value="true"/>
        </attvalues>
      </node>
    </nodes>
    <edges>
      <edge id="0" source="0" target="1" label="MULTI_ANSWER"/>
    </edges>
</graph>
```

This setup is implemented in questions.gexf. Every node and egde gets a unique id, label leads to the appropriate string_id.
```xml
<?xml version="1.0" encoding="UTF-8"?>
<gexf xmlns="http://www.gexf.net/1.2draft" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.gexf.net/1.2draft  http://www.gexf.net/1.2draft/gexf.xsd" version="1.2">
  <graph defaultedgetype="directed">
    <attributes class="node">
      <attribute id="0" title="multichoice" type="boolean">
        <default>false</default>
      </attribute>
    </attributes>
    <nodes>
      <node id="0" label="NORMAL_QUESTION"/>
      <node id="1" label="MULTI_QUESTION">
        <attvalues>
          <attvalue for="0" value="true"/>
        </attvalues>
      </node>
    </nodes>
    <edges>
      <edge id="0" source="0" target="1" label="AGE_ANSWER"/>
      <edge id="1" source="1" target="2" label="LIVING_ANSWER"/>
    </edges>
  </graph>
</gexf>
```
As you can see, half the work happens in the translation file, not here.

In case you want to look at the graph, this python code creates a .png file. You need to install `networkx` and `matplotlib`: 
```python
import matplotlib.pyplot as plt
import networkx as nx
G = nx.readwrite.read_gexf("questions.gexf")
pos = {}
x = 1
y = 1
for node in G.nodes:
    if y == 4:
        x += 1
        y = 1
    pos[node] = (x, y)
    y += 1
plt.figure(figsize=(20,20))
nx.draw_networkx(G,pos,edge_color='black',linewidths=1, node_size=[len(G.nodes()[v]["label"]) * 50 for v in G.nodes()],node_color='pink',alpha=0.9, labels={node:G.nodes()[node]["label"] for node in G.nodes()})
nx.draw_networkx_edge_labels(G,pos,edge_labels={edge:G.edges()[edge]["label"] for edge in G.edges()}, font_color="darkred")
plt.savefig("output.png", bbox_inches = "tight")
```

