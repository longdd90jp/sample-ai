package com.mcp.demo.api;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/home")
public class HomeController {

    private final RestTemplate restTemplate = new RestTemplate();
    private final ObjectMapper objectMapper;
    private final String mcpUrl;

    public HomeController(ObjectMapper objectMapper,
                          @Value("${mcp.server.url:http://localhost:8000/mcp}") String mcpUrl) {
        this.objectMapper = objectMapper;
        this.mcpUrl = mcpUrl;
    }

    @GetMapping("/process")
    public ResponseEntity<?> process(@RequestParam String input) {
        try {
            Map<String, Object> params = new LinkedHashMap<>();
            params.put("name", "process_data");
            params.put("arguments", Map.of("input", input));

            Map<String, Object> request = new LinkedHashMap<>();
            request.put("jsonrpc", "2.0");
            request.put("id", UUID.randomUUID().toString());
            request.put("method", "tools/call");
            request.put("params", params);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.setAccept(java.util.List.of(MediaType.APPLICATION_JSON));

            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(request, headers);

            ResponseEntity<JsonNode> response =
                    restTemplate.exchange(mcpUrl, HttpMethod.POST, entity, JsonNode.class);

            JsonNode body = response.getBody();
            if (body == null) {
                return ResponseEntity.status(HttpStatus.BAD_GATEWAY)
                        .body(Map.of("error", "Empty response from MCP server"));
            }

            String text = null;
            JsonNode result = body.get("result");
            if (result != null && result.has("content") && result.get("content").isArray()
                    && result.get("content").size() > 0) {
                JsonNode first = result.get("content").get(0);
                if (first.has("text")) {
                    text = first.get("text").asText();
                }
            }

            Map<String, Object> out = new LinkedHashMap<>();
            out.put("input", input);
            out.put("mcpText", text);
            out.put("raw", body);

            return ResponseEntity.ok(out);
        } catch (Exception ex) {
            return ResponseEntity.status(HttpStatus.BAD_GATEWAY)
                    .body(Map.of("error", ex.getMessage()));
        }
    }
}
