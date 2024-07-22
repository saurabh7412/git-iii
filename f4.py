package main

import (
	"context"
	"fmt"

	"github.com/google/go-genproto/googleapis/cloud/dialogflow/cx/v3beta1"
	"github.com/google/go-genproto/googleapis/cloud/language/v1"
	"github.com/google/go-genproto/googleapis/cloud/vision/v1"
	"google.golang.org/api/option"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

type HumanMessage struct {
	Content []MessagePart
}

type MessagePart struct {
	Type       string
	Text       string
	ImageURL  string
}

func main() {
	ctx := context.Background()
	// Replace with your actual Google Cloud project ID
	projectID := "your-project-id"
	// Replace with your actual Google Cloud location
	location := "us-central1"
	// Replace with your actual Google Cloud API key
	apiKey := "your-api-key"

	// Create a new Dialogflow CX client
	cxClient, err := cxv3beta1.NewSessionsClient(ctx, option.WithCredentialsFile("path/to/your/credentials.json"), option.WithEndpoint("dialogflow.googleapis.com:443"))
	if err != nil {
		panic(err)
	}
	defer cxClient.Close()

	// Create a new Vision client
	visionClient, err := vision.NewImageAnnotatorClient(ctx, option.WithCredentialsFile("path/to/your/credentials.json"))
	if err != nil {
		panic(err)
	}
	defer visionClient.Close()

	// Create a new Language client
	languageClient, err := language.NewLanguageServiceClient(ctx, option.WithCredentialsFile("path/to/your/credentials.json"))
	if err != nil {
		panic(err)
	}
	defer languageClient.Close()

	message := HumanMessage{
		Content: []MessagePart{
			{
				Type:  "text",
				Text: "What's in this image?",
			},
			{
				Type:     "image_url",
				ImageURL: "https://picsum.photos/seed/picsum/200/300",
			},
		},
	}

	// Process the message and generate a response
	response, err := processMessage(ctx, cxClient, visionClient, languageClient, message, projectID, location)
	if err != nil {
		panic(err)
	}

	fmt.Println(response)
}

// Process the message and generate a response
func processMessage(ctx context.Context, cxClient *cxv3beta1.SessionsClient, visionClient *vision.ImageAnnotatorClient, languageClient *language.LanguageServiceClient, message HumanMessage, projectID, location string) (string, error) {
	// Create a new Dialogflow CX session
	sessionID := "your-session-id"
	sessionPath := fmt.Sprintf("projects/%s/locations/%s/agents/%s/sessions/%s", projectID, location, "your-agent-id", sessionID)

	// Build the Dialogflow CX query
	query := &cxv3beta1.QueryInput{
		LanguageCode: "en-US", // Set the language code
		Text: &cxv3beta1.TextInput{
			Text: message.Content[0].Text,
		},
	}

	// Send the query to Dialogflow CX
	response, err := cxClient.DetectIntent(ctx, &cxv3beta1.DetectIntentRequest{
		Session: sessionPath,
		QueryInput: query,
	})
	if err != nil {
		return "", fmt.Errorf("failed to detect intent: %w", err)
	}

	// Analyze the image
	imageSource := &vision.ImageSource{
		ImageUri: message.Content[1].ImageURL,
	}
	image := &vision.Image{
		Source: imageSource,
	}
	annotationRequest := &vision.AnnotateImageRequest{
		Image: image,
		Features: []*vision.Feature{
			{
				Type: vision.Feature_LABEL_DETECTION,
			},
		},
	}
	annotationsResponse, err := visionClient.AnnotateImage(ctx, annotationRequest)
	if err != nil {
		return "", fmt.Errorf("failed to annotate image: %w", err)
	}

	// Process the image labels
	labels := ""
	for _, label := range annotationsResponse.LabelAnnotations {
		labels += label.Description + ", "
	}

	// Build the final response
	finalResponse := fmt.Sprintf("%s %s", response.FulfillmentText, labels)

	return finalResponse, nil
}
