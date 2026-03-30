const margin = {top: 20, right: 120, bottom: 30, left: 800};  
const svg = d3.select("#ast")
    .append("svg")
    .attr("preserveAspectRatio", "xMinYMin meet");  

function processNode(node) {
    const children = [];
    for (const key in node) {
        if (key !== 'type' && typeof node[key] === 'object') {
            if (Array.isArray(node[key])) {
                node[key].forEach(child => {
                    if (typeof child === 'object') {
                        children.push(processNode(child));
                    }
                });
            } else if (node[key] !== null) {
                children.push(processNode(node[key]));
            }
        }
    }
    return {
        name: node.type,
        children: children.length ? children : null,
        value: Object.entries(node)
            .filter(([key, val]) => key !== 'type' && typeof val !== 'object')
            .map(([key, val]) => `${key}: ${val}`)
            .join(', ')
    };
}

function downloadSVG() {
    const svgElement = document.querySelector('#ast svg');
    
    const svgClone = svgElement.cloneNode(true);
    
    const transform = d3.zoomTransform(svgElement);
    
    const g = svgClone.querySelector('g');
    if (g) {
        g.setAttribute('transform', `translate(${transform.x},${transform.y}) scale(${transform.k})`);
    }
    
    const style = document.createElement('style');
    style.textContent = `
        .link {
            fill: none;
            stroke: #ccc;
            stroke-width: 2px;
        }
        .type-node {
            stroke: #fff;
            stroke-width: 2px;
            fill: #69c;
        }
        .type-text {
            font-size: 14px;
            font-weight: bold;
            fill: #2c3e50;
            text-anchor: middle;
        }
    `;
    svgClone.insertBefore(style, svgClone.firstChild);
    
    const svgData = new XMLSerializer().serializeToString(svgClone);
    const svgBlob = new Blob([svgData], {type: "image/svg+xml;charset=utf-8"});
    const svgUrl = URL.createObjectURL(svgBlob);
    
    const downloadLink = document.createElement("a");
    downloadLink.href = svgUrl;
    downloadLink.download = "syntax_tree.svg";
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
    URL.revokeObjectURL(svgUrl);
}

fetch('/static/output/ast.json')
    .then(response => response.json())
    .then(data => {
        const root = d3.hierarchy(processNode(data));
        const descendants = root.descendants();
        const maxDepth = d3.max(descendants, d => d.depth);
        const nodeCount = descendants.length;

        const nodeHeight = 160; 
        const nodeWidth = 140; 
        const height = Math.max(nodeCount * 20, nodeCount * nodeHeight / (maxDepth + 1));
        const width = Math.max((maxDepth + 1) * nodeWidth, 800);

        const tree = d3.tree()
            .size([width, height])
            .nodeSize([width / (maxDepth + 1), nodeHeight]);

        tree(root);

        const x0 = d3.min(root.descendants(), d => d.x);
        const x1 = d3.max(root.descendants(), d => d.x);
        const y0 = d3.min(root.descendants(), d => d.y);
        const y1 = d3.max(root.descendants(), d => d.y);

        const nodeRadius = 70; 
        const actualWidth = x1 - x0 + nodeRadius * 2 + margin.left + margin.right;
        const actualHeight = y1 - y0 + nodeRadius * 2 + margin.top + margin.bottom;
        
        svg
            .attr("width", actualWidth)
            .attr("height", actualHeight)
            .attr("viewBox", `0 0 ${actualWidth} ${actualHeight}`);


        const minScale = Math.max(0.1, 400 / (actualWidth + actualHeight));
        const maxScale = Math.min(4, Math.max(1.5, (nodeCount / 100)));

        const zoom = d3.zoom()
            .scaleExtent([minScale, maxScale])
            .on("zoom", (event) => {
                g.attr("transform", event.transform);
            });


        svg.call(zoom);

        const leftmostX = x0 - nodeRadius; 
        const g = svg.append("g")
            .attr("transform", `translate(${margin.left - leftmostX},${margin.top - y0 + nodeRadius})`);

        g.selectAll(".link")
            .data(root.links())
            .enter()
            .append("path")
            .attr("class", "link")
            .attr("d", d3.linkVertical()
                .x(d => d.x)
                .y(d => d.y));

        const node = g.selectAll(".node")
            .data(root.descendants())
            .enter()
            .append("g")
            .attr("class", "node")
            .attr("transform", d => `translate(${d.x},${d.y})`);

        node.append("ellipse")
            .attr("class", "type-node")
            .attr("rx", 70)  
            .attr("ry", 35)
            .style("fill", "#69c");

        node.append("text")
            .attr("class", "type-text")
            .attr("dy", ".3em")
            .attr("text-anchor", "middle")
            .text(d => d.data.name);

        const tooltip = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("opacity", 0)
            .style("position", "absolute")
            .style("background-color", "white")
            .style("border", "1px solid #ddd")
            .style("padding", "10px")
            .style("border-radius", "5px")
            .style("pointer-events", "none");

        node.on("mouseover", function(event, d) {
            if (d.data.value) {
                tooltip.transition()
                    .duration(200)
                    .style("opacity", .9);
                tooltip.html(d.data.value)
                    .style("left", (event.pageX + 10) + "px")
                    .style("top", (event.pageY - 28) + "px");
            }
        })
        .on("mouseout", function(d) {
            tooltip.transition()
                .duration(500)
                .style("opacity", 0);
        });

        svg.on("wheel", function(event) {
            event.preventDefault();
            const currentTransform = d3.zoomTransform(svg.node());
            const scale = event.deltaY < 0 ? 1.1 : 0.9;
            const newScale = currentTransform.k * scale;
            
            if (newScale >= minScale && newScale <= maxScale) {
                const mouseX = event.offsetX;
                const mouseY = event.offsetY;
                
                const newTransform = currentTransform
                    .translate(mouseX, mouseY)
                    .scale(newScale)
                    .translate(-mouseX, -mouseY);
                
                svg.transition()
                    .duration(50)
                    .call(zoom.transform, newTransform);
            }
        });

        const container = document.getElementById('ast-container');
        const initialScale = Math.min(
            container.clientWidth / actualWidth,
            container.clientHeight / actualHeight
        ) * 0.8;
        // 计算初始位置，确保从左上角开始显示
        const initialX = margin.left;
        const initialY = margin.top;

        svg.call(zoom.transform, d3.zoomIdentity
            .translate(initialX, initialY)
            .scale(initialScale)
        );

        document.getElementById('download-svg').addEventListener('click', downloadSVG);
    })
    .catch(error => {
        console.error('Error loading AST:', error);
        document.getElementById("ast").innerHTML = "Error loading AST visualization";
    });
