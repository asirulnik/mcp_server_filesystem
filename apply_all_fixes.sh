#!/bin/bash

# Enhanced fix script for MCP Outlook Server
# Created: April 18, 2025
# Description: Systematically fixes TypeScript errors in the MCP Outlook codebase

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Define the project root directory
PROJECT_ROOT="/Users/andrewsirulnik/claude_mcp_servers/mcp-outlook"
cd "$PROJECT_ROOT" || { echo -e "${RED}Failed to navigate to project directory${NC}"; exit 1; }

# Helper function for displaying steps
print_step() {
  echo -e "${GREEN}Step $1: $2${NC}"
}

# Helper function for displaying warnings
print_warning() {
  echo -e "${YELLOW}Warning: $1${NC}"
}

# Helper function to log errors to bug collection
log_error() {
  local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
  local command="$1"
  local error_message="$2"
  local insight="$3"
  
  echo "[ERROR] $timestamp" >> bug_collection.log
  echo "Command: $command" >> bug_collection.log
  echo "Error: $error_message" >> bug_collection.log
  echo "Insight: $insight" >> bug_collection.log
  echo "--------------------------" >> bug_collection.log
}

# Create backup directory
mkdir -p fix_backups/$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="fix_backups/$(date +"%Y%m%d_%H%M%S")"
echo -e "${GREEN}Created backup directory: $BACKUP_DIR${NC}"

# Step 1: Fix Service Factory and Instantiation Issues
print_step "1" "Fixing Service Factory and Instantiation Issues"

# Backup original files
cp src/services/mailService/index.ts "$BACKUP_DIR/"
cp src/services/adapters.ts "$BACKUP_DIR/"
cp src/services/adapters.fixed.ts "$BACKUP_DIR/" 2>/dev/null || true

# Update Service Instantiations in index.ts
cat > src/services/mailService/index.ts << 'EOF'
import { IEmailService } from '../interfaces/emailService';
import { IFolderService } from '../interfaces/folderService';
import { IDraftService } from '../interfaces/draftService';
import { ICalendarService } from '../interfaces/calendarService';
import { IAuthService } from '../interfaces/authService';

import { EmailService } from './emailService_fixed';
import { FolderService } from './folderService';
import { DraftService } from './draftService';
import { CalendarService } from './calendar/calendarService_fixed';
import { AuthService } from '../authService.fixed';

// Create a singleton instance of AuthService to share
const authServiceInstance = new AuthService();

// Create service instances with proper dependencies
const folderServiceInstance = new FolderService(authServiceInstance);
const emailServiceInstance = new EmailService(authServiceInstance, folderServiceInstance);
const draftServiceInstance = new DraftService(authServiceInstance);
const calendarServiceInstance = new CalendarService(authServiceInstance);

// Export service instances
export const folderService: IFolderService = folderServiceInstance;
export const emailService: IEmailService = emailServiceInstance;
export const draftService: IDraftService = draftServiceInstance;
export const calendarService: ICalendarService = calendarServiceInstance;
export const authService: IAuthService = authServiceInstance;
EOF

# Step 2: Fix Type Compatibility Utilities
print_step "2" "Fixing Type Compatibility Utilities"

# Backup original file
cp src/services/type_compatibility.ts "$BACKUP_DIR/"

# Create enhanced type_compatibility.ts with fixed generateShortId function
cat > src/services/type_compatibility_fixed.ts << 'EOF'
import { EntityType } from '../models/common';
import * as crypto from 'crypto';

/**
 * Generates a short ID based on a longer ID and an entity type
 * @param id The original ID to shorten
 * @param entityType The type of entity this ID represents
 * @param length Optional length for the generated ID (default: 8)
 * @returns A shortened ID string
 */
export function generateShortId(id: string, entityType?: EntityType, length: number = 8): string {
  if (!id) {
    return '';
  }
  
  // Use entityType as a prefix if available
  const prefix = entityType ? `${entityType.substring(0, 2)}_` : '';
  
  // Create a hash of the original ID
  const hash = crypto.createHash('sha256').update(id).digest('hex');
  
  // Return a substring of the hash with the prefix
  return `${prefix}${hash.substring(0, length)}`;
}

/**
 * Safely converts a date to ISO string format
 * @param date The date to convert
 * @returns ISO string representation or undefined
 */
export function toISOString(date: Date | string | undefined): string | undefined {
  if (!date) {
    return undefined;
  }
  
  try {
    if (typeof date === 'string') {
      return new Date(date).toISOString();
    }
    return date.toISOString();
  } catch (error) {
    console.error('Error converting date to ISO string:', error);
    return undefined;
  }
}

/**
 * Creates a safe copy of an object with null protection
 * @param obj The object to copy
 * @returns A safe copy of the object
 */
export function safeCopy<T>(obj: T | null | undefined): Partial<T> {
  if (!obj) {
    return {};
  }
  return { ...obj };
}

// Export all utilities for use in service implementations
export default {
  generateShortId,
  toISOString,
  safeCopy
};
EOF

# Step 3: Fix Service Adapters
print_step "3" "Fixing Service Adapters"

# Create fixed adapters.ts with type safety improvements
cat > src/services/adapters.fixed.ts << 'EOF'
import { IEmailService } from './interfaces/emailService';
import { IFolderService } from './interfaces/folderService';
import { IDraftService } from './interfaces/draftService';
import { ICalendarService } from './interfaces/calendarService';
import { IAuthService } from './interfaces/authService';

import { EmailService } from './mailService/emailService_fixed';
import { FolderService } from './mailService/folderService';
import { DraftService } from './mailService/draftService';
import { CalendarService } from './mailService/calendar/calendarService_fixed';
import { AuthService } from './authService.fixed';

import { EmailDetails, EmailMessage, EmailSearchOptions } from '../models/email';
import { MailFolder, NewMailFolder } from '../models/folder';
import { DraftMessage } from '../models/draft';
import { Calendar, CalendarEvent, NewCalendarEvent, CalendarSearchOptions } from '../models/calendar';
import { EntityType } from '../models/common';
import { generateShortId } from './type_compatibility_fixed';

/**
 * Creates an adapter for the email service that ensures interface compatibility
 * @param emailService The email service implementation to adapt
 * @returns An adapter that implements IEmailService
 */
export function createEmailServiceAdapter(emailService: EmailService): IEmailService {
  return {
    async getEmails(folderIdOrPath: string, options?: EmailSearchOptions) {
      const result = await emailService.getEmails(folderIdOrPath, options);
      if (!result || !Array.isArray(result)) {
        return [];
      }
      
      return result.map(email => ({
        id: email.id || '',
        shortId: email.shortId || generateShortId(email.id || '', EntityType.Email),
        subject: email.subject || '',
        from: email.from || { emailAddress: { address: '', name: '' } },
        toRecipients: email.toRecipients || [],
        ccRecipients: email.ccRecipients || [],
        bccRecipients: email.bccRecipients || [],
        receivedDateTime: email.receivedDateTime || new Date().toISOString(),
        hasAttachments: email.hasAttachments || false,
        bodyPreview: email.bodyPreview || '',
        importance: email.importance || 'normal',
        isRead: email.isRead || false,
        folderId: email.folderId || ''
      }));
    },

    async getEmail(emailId: string) {
      const result = await emailService.getEmail(emailId);
      if (!result) {
        throw new Error(`Email with ID ${emailId} not found`);
      }
      
      return {
        id: result.id || '',
        shortId: result.shortId || generateShortId(result.id || '', EntityType.Email),
        subject: result.subject || '',
        from: result.from || { emailAddress: { address: '', name: '' } },
        toRecipients: result.toRecipients || [],
        ccRecipients: result.ccRecipients || [],
        bccRecipients: result.bccRecipients || [],
        receivedDateTime: result.receivedDateTime || new Date().toISOString(),
        body: result.body || { content: '', contentType: 'text' },
        attachments: result.attachments || [],
        hasAttachments: result.hasAttachments || false,
        importance: result.importance || 'normal',
        internetMessageId: result.internetMessageId || '',
        isRead: result.isRead || false
      };
    },

    async sendEmail(email: EmailMessage) {
      return await emailService.sendEmail(email);
    },

    async replyToEmail(emailId: string, message: string, replyAll?: boolean) {
      return await emailService.replyToEmail(emailId, message, replyAll);
    },

    async forwardEmail(emailId: string, message: string, toRecipients: Array<{ emailAddress: { address: string; name?: string } }>) {
      return await emailService.forwardEmail(emailId, message, toRecipients);
    },

    async moveEmail(emailId: string, destinationFolderId: string) {
      return await emailService.moveEmail(emailId, destinationFolderId);
    },

    async copyEmail(emailId: string, destinationFolderId: string) {
      return await emailService.copyEmail(emailId, destinationFolderId);
    },

    async markAsRead(emailId: string, isRead: boolean) {
      return await emailService.markAsRead(emailId, isRead);
    },

    async deleteEmail(emailId: string) {
      return await emailService.deleteEmail(emailId);
    }
  };
}

/**
 * Creates an adapter for the folder service that ensures interface compatibility
 * @param folderService The folder service implementation to adapt
 * @returns An adapter that implements IFolderService
 */
export function createFolderServiceAdapter(folderService: FolderService): IFolderService {
  return {
    async getFolders(userEmail: string) {
      return await folderService.getFolders(userEmail);
    },

    async getFolder(folderIdOrPath: string) {
      return await folderService.getFolder(folderIdOrPath);
    },

    async createFolder(folder: NewMailFolder) {
      return await folderService.createFolder(folder);
    },

    async updateFolder(folderId: string, folder: Partial<MailFolder>) {
      return await folderService.updateFolder(folderId, folder);
    },

    async deleteFolder(folderId: string) {
      return await folderService.deleteFolder(folderId);
    },

    async moveFolder(folderId: string, destinationFolderId: string) {
      return await folderService.moveFolder(folderId, destinationFolderId);
    },

    // Add implementation for buildFolderPathMap if needed
    async buildFolderPathMap(userEmail: string) {
      if (typeof folderService.buildFolderPathMap === 'function') {
        return await folderService.buildFolderPathMap(userEmail);
      }
      return {};
    },

    // Add implementation for copyFolder if needed
    async copyFolder(folderId: string, destinationFolderId: string) {
      if (typeof folderService.copyFolder === 'function') {
        return await folderService.copyFolder(folderId, destinationFolderId);
      }
      throw new Error('copyFolder method not implemented');
    }
  };
}

/**
 * Creates an adapter for the draft service that ensures interface compatibility
 * @param draftService The draft service implementation to adapt
 * @returns An adapter that implements IDraftService
 */
export function createDraftServiceAdapter(draftService: DraftService): IDraftService {
  return {
    async getDrafts() {
      return await draftService.getDrafts();
    },

    async getDraft(draftId: string) {
      return await draftService.getDraft(draftId);
    },

    async createDraft(draft: DraftMessage) {
      return await draftService.createDraft(draft);
    },

    async updateDraft(draftId: string, draft: Partial<DraftMessage>) {
      return await draftService.updateDraft(draftId, draft);
    },

    async deleteDraft(draftId: string) {
      return await draftService.deleteDraft(draftId);
    },

    async sendDraft(draftId: string) {
      return await draftService.sendDraft(draftId);
    }
  };
}

/**
 * Creates an adapter for the calendar service that ensures interface compatibility
 * @param calendarService The calendar service implementation to adapt
 * @returns An adapter that implements ICalendarService
 */
export function createCalendarServiceAdapter(calendarService: CalendarService): ICalendarService {
  return {
    async getCalendars() {
      return await calendarService.getCalendars();
    },

    async getCalendar(calendarId: string) {
      return await calendarService.getCalendar(calendarId);
    },

    async getEvents(calendarId: string, options?: CalendarSearchOptions) {
      return await calendarService.getEvents(calendarId, options);
    },

    async getEvent(calendarId: string, eventId: string) {
      return await calendarService.getEvent(calendarId, eventId);
    },

    async createEvent(calendarId: string, event: NewCalendarEvent) {
      return await calendarService.createEvent(calendarId, event);
    },

    async updateEvent(calendarId: string, eventId: string, event: Partial<CalendarEvent>) {
      return await calendarService.updateEvent(calendarId, eventId, event);
    },

    async deleteEvent(calendarId: string, eventId: string) {
      return await calendarService.deleteEvent(calendarId, eventId);
    }
  };
}

/**
 * Creates an adapter for the auth service that ensures interface compatibility
 * @param authService The auth service implementation to adapt
 * @returns An adapter that implements IAuthService
 */
export function createAuthServiceAdapter(authService: AuthService): IAuthService {
  return {
    async authenticate() {
      return await authService.authenticate();
    },

    async getAccessToken() {
      return await authService.getAccessToken();
    },

    async getAuthenticatedClient() {
      return await authService.getAuthenticatedClient();
    },

    async testAuthentication() {
      return await authService.testAuthentication();
    }
  };
}

// Service factory functions with proper dependency injection
export function getAuthService(): IAuthService {
  return createAuthServiceAdapter(new AuthService());
}

export function getFolderService(): IFolderService {
  const authService = new AuthService();
  return createFolderServiceAdapter(new FolderService(authService));
}

export function getEmailService(): IEmailService {
  const authService = new AuthService();
  const folderService = new FolderService(authService);
  return createEmailServiceAdapter(new EmailService(authService, folderService));
}

export function getDraftService(): IDraftService {
  const authService = new AuthService();
  return createDraftServiceAdapter(new DraftService(authService));
}

export function getCalendarService(): ICalendarService {
  const authService = new AuthService();
  return createCalendarServiceAdapter(new CalendarService(authService));
}
EOF

# Step 4: Fix Interface Implementations - Calendar Service
print_step "4" "Fixing Calendar Service Implementation"

# Backup original file
cp src/services/mailService/calendar/calendarService_fixed.ts "$BACKUP_DIR/" 2>/dev/null || true

# Create a fixed calendar service implementation
cat > src/services/mailService/calendar/calendarService_fixed.ts << 'EOF'
import { ICalendarService } from '../../interfaces/calendarService';
import { IAuthService } from '../../interfaces/authService';
import { Calendar, CalendarEvent, NewCalendarEvent, CalendarSearchOptions } from '../../../models/calendar';
import { EntityType } from '../../../models/common';
import * as TypeCompat from '../../type_compatibility_fixed';
import * as MicrosoftGraph from '@microsoft/microsoft-graph-client';

/**
 * Service implementation for Microsoft Outlook Calendar operations
 */
export class CalendarService implements ICalendarService {
  private authService: IAuthService;

  /**
   * Creates a new instance of CalendarService
   * @param authService Authentication service for API access
   */
  constructor(authService: IAuthService) {
    this.authService = authService;
  }

  /**
   * Get all calendars for the authenticated user
   * @returns Array of calendars
   */
  async getCalendars(): Promise<Calendar[]> {
    try {
      const client = await this.authService.getAuthenticatedClient();
      const response = await client.api('/me/calendars').get();

      if (!response || !response.value) {
        return [];
      }

      return response.value.map((calendar: any) => ({
        id: calendar.id,
        shortId: TypeCompat.generateShortId(calendar.id, EntityType.Calendar),
        name: calendar.name || '',
        owner: calendar.owner?.name || '',
        canEdit: calendar.canEdit || false,
        canShare: calendar.canShare || false,
        canViewPrivateItems: calendar.canViewPrivateItems || false
      }));
    } catch (error) {
      console.error('Error fetching calendars:', error);
      throw new Error(`Failed to get calendars: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Get a specific calendar by ID
   * @param calendarId ID of the calendar to retrieve
   * @returns The calendar details
   */
  async getCalendar(calendarId: string): Promise<Calendar> {
    try {
      const client = await this.authService.getAuthenticatedClient();
      const calendar = await client.api(`/me/calendars/${calendarId}`).get();

      if (!calendar) {
        throw new Error(`Calendar with ID ${calendarId} not found`);
      }

      return {
        id: calendar.id,
        shortId: TypeCompat.generateShortId(calendar.id, EntityType.Calendar),
        name: calendar.name || '',
        owner: calendar.owner?.name || '',
        canEdit: calendar.canEdit || false,
        canShare: calendar.canShare || false,
        canViewPrivateItems: calendar.canViewPrivateItems || false
      };
    } catch (error) {
      console.error(`Error fetching calendar ${calendarId}:`, error);
      throw new Error(`Failed to get calendar: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Get events from a specified calendar with optional filtering
   * @param calendarId ID of the calendar to get events from
   * @param options Optional search parameters
   * @returns Array of calendar events
   */
  async getEvents(calendarId: string, options?: CalendarSearchOptions): Promise<CalendarEvent[]> {
    try {
      const client = await this.authService.getAuthenticatedClient();
      let apiUrl = `/me/calendars/${calendarId}/events`;

      // Build query parameters based on options
      const queryParams: string[] = [];
      if (options) {
        if (options.startDateTime) {
          queryParams.push(`startDateTime=${encodeURIComponent(new Date(options.startDateTime).toISOString())}`);
        }
        if (options.endDateTime) {
          queryParams.push(`endDateTime=${encodeURIComponent(new Date(options.endDateTime).toISOString())}`);
        }
        if (options.limit && options.limit > 0) {
          queryParams.push(`$top=${options.limit}`);
        }
      }

      // Append query parameters to API URL
      if (queryParams.length > 0) {
        apiUrl += `?${queryParams.join('&')}`;
      }

      const response = await client.api(apiUrl).get();

      if (!response || !response.value) {
        return [];
      }

      return response.value.map((event: any) => {
        return {
          id: event.id,
          shortId: TypeCompat.generateShortId(event.id, EntityType.Event),
          subject: event.subject || '',
          bodyPreview: event.bodyPreview || '',
          body: event.body || { contentType: 'text', content: '' },
          start: event.start || { dateTime: new Date().toISOString(), timeZone: 'UTC' },
          end: event.end || { dateTime: new Date().toISOString(), timeZone: 'UTC' },
          location: event.location?.displayName || '',
          organizer: event.organizer || { emailAddress: { name: '', address: '' } },
          attendees: Array.isArray(event.attendees) ? event.attendees : [],
          isAllDay: event.isAllDay || false,
          isCancelled: event.isCancelled || false,
          isOnlineMeeting: event.isOnlineMeeting || false,
          onlineMeetingUrl: event.onlineMeetingUrl || '',
          recurrence: event.recurrence || null,
          timeZone: event.originalStartTimeZone || 'UTC', // Add required timeZone property
          bodyContentType: event.body?.contentType || 'text' // Add required bodyContentType property
          // Use a custom property or include showAs in a compatible way
          // showAs: event.showAs || 'busy',
        };
      });
    } catch (error) {
      console.error(`Error fetching events for calendar ${calendarId}:`, error);
      throw new Error(`Failed to get events: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }
EOF

cat >> src/services/mailService/calendar/calendarService_fixed.ts << 'EOF'
  /**
   * Get a specific event from a calendar
   * @param calendarId ID of the calendar containing the event
   * @param eventId ID of the event to retrieve
   * @returns The event details
   */
  async getEvent(calendarId: string, eventId: string): Promise<CalendarEvent> {
    try {
      const client = await this.authService.getAuthenticatedClient();
      const event = await client.api(`/me/calendars/${calendarId}/events/${eventId}`).get();

      if (!event) {
        throw new Error(`Event with ID ${eventId} not found in calendar ${calendarId}`);
      }

      return {
        id: event.id,
        shortId: TypeCompat.generateShortId(event.id, EntityType.Event),
        subject: event.subject || '',
        bodyPreview: event.bodyPreview || '',
        body: event.body || { contentType: 'text', content: '' },
        start: event.start || { dateTime: new Date().toISOString(), timeZone: 'UTC' },
        end: event.end || { dateTime: new Date().toISOString(), timeZone: 'UTC' },
        location: event.location?.displayName || '',
        organizer: event.organizer || { emailAddress: { name: '', address: '' } },
        attendees: Array.isArray(event.attendees) ? event.attendees : [],
        isAllDay: event.isAllDay || false,
        isCancelled: event.isCancelled || false,
        isOnlineMeeting: event.isOnlineMeeting || false,
        onlineMeetingUrl: event.onlineMeetingUrl || '',
        recurrence: event.recurrence || null,
        timeZone: event.originalStartTimeZone || 'UTC', // Add required timeZone property
        bodyContentType: event.body?.contentType || 'text' // Add required bodyContentType property
      };
    } catch (error) {
      console.error(`Error fetching event ${eventId} from calendar ${calendarId}:`, error);
      throw new Error(`Failed to get event: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Create a new event in a calendar
   * @param calendarId ID of the calendar to create the event in
   * @param options Details for the new event
   * @returns The created event
   */
  async createEvent(calendarId: string, options: NewCalendarEvent): Promise<CalendarEvent> {
    try {
      const client = await this.authService.getAuthenticatedClient();
      
      // Convert date parameters to expected format
      const eventPayload: any = {
        subject: options.subject,
        body: {
          contentType: options.bodyContentType || 'text',
          content: options.body || ''
        },
        start: {
          dateTime: typeof options.start === 'string' ? new Date(options.start).toISOString().slice(0, 19) : options.start.dateTime,
          timeZone: (typeof options.start === 'object' && options.start.timeZone) ? options.start.timeZone : options.timeZone || 'UTC'
        },
        end: {
          dateTime: typeof options.end === 'string' ? new Date(options.end).toISOString().slice(0, 19) : options.end.dateTime,
          timeZone: (typeof options.end === 'object' && options.end.timeZone) ? options.end.timeZone : options.timeZone || 'UTC'
        },
        location: {
          displayName: options.location || ''
        },
        isAllDay: options.isAllDay || false,
        isOnlineMeeting: options.isOnlineMeeting || false
      };

      // Add attendees if provided
      if (options.attendees) {
        if (Array.isArray(options.attendees)) {
          eventPayload.attendees = options.attendees.map(attendee => {
            if (typeof attendee === 'string') {
              return {
                emailAddress: { address: attendee },
                type: 'required'
              };
            }
            return attendee;
          });
        } else if (typeof options.attendees === 'string') {
          eventPayload.attendees = [{
            emailAddress: { address: options.attendees },
            type: 'required'
          }];
        }
      }

      const response = await client.api(`/me/calendars/${calendarId}/events`).post(eventPayload);

      if (!response) {
        throw new Error('Failed to create event: No response received');
      }

      return {
        id: response.id,
        shortId: TypeCompat.generateShortId(response.id, EntityType.Event),
        subject: response.subject || '',
        bodyPreview: response.bodyPreview || '',
        body: response.body || { contentType: 'text', content: '' },
        start: response.start || { dateTime: new Date().toISOString(), timeZone: 'UTC' },
        end: response.end || { dateTime: new Date().toISOString(), timeZone: 'UTC' },
        location: response.location?.displayName || '',
        organizer: response.organizer || { emailAddress: { name: '', address: '' } },
        attendees: Array.isArray(response.attendees) ? response.attendees : [],
        isAllDay: response.isAllDay || false,
        isCancelled: response.isCancelled || false,
        isOnlineMeeting: response.isOnlineMeeting || false,
        onlineMeetingUrl: response.onlineMeetingUrl || '',
        recurrence: response.recurrence || null,
        timeZone: response.originalStartTimeZone || options.timeZone || 'UTC',
        bodyContentType: response.body?.contentType || options.bodyContentType || 'text'
      };
    } catch (error) {
      console.error(`Error creating event in calendar ${calendarId}:`, error);
      throw new Error(`Failed to create event: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }
EOF

cat >> src/services/mailService/calendar/calendarService_fixed.ts << 'EOF'
  /**
   * Update an existing event in a calendar
   * @param calendarId ID of the calendar containing the event
   * @param eventId ID of the event to update
   * @param options New details for the event
   * @returns The updated event
   */
  async updateEvent(calendarId: string, eventId: string, options: Partial<CalendarEvent>): Promise<CalendarEvent> {
    try {
      const client = await this.authService.getAuthenticatedClient();
      
      // Build update payload based on provided options
      const updatePayload: any = {};

      if (options.subject) {
        updatePayload.subject = options.subject;
      }

      if (options.body) {
        updatePayload.body = {
          contentType: options.bodyContentType || 'text',
          content: options.body.content || ''
        };
      }

      if (options.start) {
        updatePayload.start = {
          dateTime: typeof options.start === 'string' 
            ? new Date(options.start).toISOString().slice(0, 19) 
            : options.start.dateTime,
          timeZone: (typeof options.start === 'object' && options.start.timeZone) 
            ? options.start.timeZone 
            : options.timeZone || 'UTC'
        };
      }

      if (options.end) {
        updatePayload.end = {
          dateTime: typeof options.end === 'string' 
            ? new Date(options.end).toISOString().slice(0, 19) 
            : options.end.dateTime,
          timeZone: (typeof options.end === 'object' && options.end.timeZone) 
            ? options.end.timeZone 
            : options.timeZone || 'UTC'
        };
      }

      if (options.location) {
        updatePayload.location = {
          displayName: options.location
        };
      }

      if (typeof options.isAllDay === 'boolean') {
        updatePayload.isAllDay = options.isAllDay;
      }

      if (typeof options.isOnlineMeeting === 'boolean') {
        updatePayload.isOnlineMeeting = options.isOnlineMeeting;
      }

      // Handle attendees with proper type checking
      if (options.attendees) {
        if (Array.isArray(options.attendees)) {
          updatePayload.attendees = options.attendees.map(attendee => {
            if (typeof attendee === 'string') {
              return {
                emailAddress: { address: attendee },
                type: 'required'
              };
            }
            return attendee;
          });
        } else if (typeof options.attendees === 'string') {
          updatePayload.attendees = [{
            emailAddress: { address: options.attendees },
            type: 'required'
          }];
        }
      }

      const response = await client.api(`/me/calendars/${calendarId}/events/${eventId}`).patch(updatePayload);

      if (!response) {
        throw new Error('Failed to update event: No response received');
      }

      return {
        id: response.id,
        shortId: TypeCompat.generateShortId(response.id, EntityType.Event),
        subject: response.subject || '',
        bodyPreview: response.bodyPreview || '',
        body: response.body || { contentType: 'text', content: '' },
        start: response.start || { dateTime: new Date().toISOString(), timeZone: 'UTC' },
        end: response.end || { dateTime: new Date().toISOString(), timeZone: 'UTC' },
        location: response.location?.displayName || '',
        organizer: response.organizer || { emailAddress: { name: '', address: '' } },
        attendees: Array.isArray(response.attendees) ? response.attendees : [],
        isAllDay: response.isAllDay || false,
        isCancelled: response.isCancelled || false,
        isOnlineMeeting: response.isOnlineMeeting || false,
        onlineMeetingUrl: response.onlineMeetingUrl || '',
        recurrence: response.recurrence || null,
        timeZone: response.originalStartTimeZone || options.timeZone || 'UTC',
        bodyContentType: response.body?.contentType || options.bodyContentType || 'text'
      };
    } catch (error) {
      console.error(`Error updating event ${eventId} in calendar ${calendarId}:`, error);
      throw new Error(`Failed to update event: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Delete an event from a calendar
   * @param calendarId ID of the calendar containing the event
   * @param eventId ID of the event to delete
   * @returns True if deletion was successful
   */
  async deleteEvent(calendarId: string, eventId: string): Promise<boolean> {
    try {
      const client = await this.authService.getAuthenticatedClient();
      await client.api(`/me/calendars/${calendarId}/events/${eventId}`).delete();
      return true;
    } catch (error) {
      console.error(`Error deleting event ${eventId} from calendar ${calendarId}:`, error);
      throw new Error(`Failed to delete event: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }
}
EOF

# Step 5: Fix Email Service Implementation
print_step "5" "Fixing Email Service Implementation"

# Backup original file
cp src/services/mailService/emailService_fixed.ts "$BACKUP_DIR/" 2>/dev/null || true

# Create fixed email service implementation
cat > src/services/mailService/emailService_fixed.ts << 'EOF'
import { IEmailService } from '../../interfaces/emailService';
import { IAuthService } from '../../interfaces/authService';
import { IFolderService } from '../../interfaces/folderService';
import { 
  EmailMessage, 
  EmailDetails, 
  EmailAttachment, 
  EmailSearchOptions 
} from '../../../models/email';
import { EntityType } from '../../../models/common';
import * as TypeCompat from '../../type_compatibility_fixed';
import * as MicrosoftGraph from '@microsoft/microsoft-graph-client';

/**
 * Service implementation for Microsoft Outlook Email operations
 */
export class EmailService implements IEmailService {
  private authService: IAuthService;
  private folderService: IFolderService;

  /**
   * Creates a new instance of EmailService
   * @param authService Authentication service for API access
   * @param folderService Service for folder operations
   */
  constructor(authService: IAuthService, folderService: IFolderService) {
    this.authService = authService;
    this.folderService = folderService;
  }

  /**
   * Get emails from a specific folder
   * @param folderIdOrPath ID or path of the folder to get emails from
   * @param options Optional search parameters
   * @returns Array of email messages
   */
  async getEmails(folderIdOrPath: string, options?: EmailSearchOptions): Promise<EmailMessage[]> {
    try {
      const client = await this.authService.getAuthenticatedClient();
      
      // Resolve folder ID if path is provided
      let folderId = folderIdOrPath;
      if (folderIdOrPath.includes('/')) {
        const folder = await this.folderService.getFolder(folderIdOrPath);
        folderId = folder.id;
      }
      
      // Build query parameters
      let queryParams = [];
      
      // Add filtering options if provided
      if (options) {
        if (options.filter) {
          queryParams.push(`$filter=${encodeURIComponent(options.filter)}`);
        }
        if (options.search) {
          queryParams.push(`$search=${encodeURIComponent('"' + options.search + '"')}`);
        }
        if (options.limit && options.limit > 0) {
          queryParams.push(`$top=${options.limit}`);
        }
        if (options.orderBy) {
          queryParams.push(`$orderby=${encodeURIComponent(options.orderBy)}`);
        }
      }
      
      // Build the API URL
      let apiUrl = `/me/mailFolders/${folderId}/messages`;
      if (queryParams.length > 0) {
        apiUrl += `?${queryParams.join('&')}`;
      }
      
      const response = await client.api(apiUrl).get();
      
      if (!response || !response.value) {
        return [];
      }
      
      return response.value.map((email: any) => ({
        id: email.id,
        shortId: TypeCompat.generateShortId(email.id, EntityType.Email),
        subject: email.subject || '',
        from: email.from || { emailAddress: { address: '', name: '' } },
        toRecipients: email.toRecipients || [],
        ccRecipients: email.ccRecipients || [],
        bccRecipients: email.bccRecipients || [],
        receivedDateTime: email.receivedDateTime || new Date().toISOString(),
        hasAttachments: email.hasAttachments || false,
        bodyPreview: email.bodyPreview || '',
        importance: email.importance || 'normal',
        isRead: email.isRead || false,
        folderId: folderId
      }));
    } catch (error) {
      console.error(`Error fetching emails from folder ${folderIdOrPath}:`, error);
      throw new Error(`Failed to get emails: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Get details of a specific email
   * @param emailId ID of the email to retrieve
   * @returns The email details
   */
  async getEmail(emailId: string): Promise<EmailDetails> {
    try {
      const client = await this.authService.getAuthenticatedClient();
      
      // Get email details with expanded attachments
      const email = await client.api(`/me/messages/${emailId}`)
        .expand('attachments')
        .get();
      
      if (!email) {
        throw new Error(`Email with ID ${emailId} not found`);
      }
      
      // Format attachments
      const attachments: EmailAttachment[] = [];
      if (email.attachments && Array.isArray(email.attachments)) {
        email.attachments.forEach((attachment: any) => {
          attachments.push({
            id: attachment.id,
            name: attachment.name || '',
            contentType: attachment.contentType || '',
            size: attachment.size || 0,
            contentId: attachment.contentId || '',
            contentBytes: attachment.contentBytes || '',
            isInline: false // Replace with actual value if available
          });
        });
      }
      
      return {
        id: email.id,
        shortId: TypeCompat.generateShortId(email.id, EntityType.Email),
        subject: email.subject || '',
        from: email.from || { emailAddress: { address: '', name: '' } },
        toRecipients: email.toRecipients || [],
        ccRecipients: email.ccRecipients || [],
        bccRecipients: email.bccRecipients || [],
        receivedDateTime: email.receivedDateTime || new Date().toISOString(),
        body: email.body || { content: '', contentType: 'text' },
        attachments: attachments,
        hasAttachments: email.hasAttachments || false,
        importance: email.importance || 'normal',
        internetMessageId: email.internetMessageId || '',
        isRead: email.isRead || false
        // Don't include folderId as it's not in the EmailDetails interface
        // parentFolderId: email.parentFolderId || ''
      };
    } catch (error) {
      console.error(`Error fetching email ${emailId}:`, error);
      throw new Error(`Failed to get email: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Send a new email
   * @param email Email message to send
   * @returns Boolean indicating success
   */
  async sendEmail(email: EmailMessage): Promise<boolean> {
    try {
      const client = await this.authService.getAuthenticatedClient();
      
      // Prepare message for sending
      const message: any = {
        subject: email.subject || '',
        body: {
          contentType: email.body?.contentType || 'text',
          content: email.body?.content || ''
        },
        toRecipients: email.toRecipients || [],
        ccRecipients: email.ccRecipients || [],
        bccRecipients: email.bccRecipients || []
      };
      
      if (email.attachments && email.attachments.length > 0) {
        message.attachments = email.attachments.map(attachment => ({
          '@odata.type': '#microsoft.graph.fileAttachment',
          name: attachment.name,
          contentType: attachment.contentType,
          contentBytes: attachment.contentBytes,
          contentId: attachment.contentId,
          isInline: attachment.isInline || false
        }));
      }
      
      // Send the message
      await client.api('/me/sendMail').post({
        message: message,
        saveToSentItems: true
      });
      
      return true;
    } catch (error) {
      console.error(`Error sending email:`, error);
      throw new Error(`Failed to send email: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Reply to an email
   * @param emailId ID of the email to reply to
   * @param message Reply message content
   * @param replyAll Whether to reply to all recipients
   * @returns Boolean indicating success
   */
  async replyToEmail(emailId: string, message: string, replyAll?: boolean): Promise<boolean> {
    try {
      const client = await this.authService.getAuthenticatedClient();
      
      // Choose appropriate API endpoint based on replyAll flag
      const endpoint = replyAll ? 'replyAll' : 'reply';
      
      // Send reply
      await client.api(`/me/messages/${emailId}/${endpoint}`).post({
        comment: message
      });
      
      return true;
    } catch (error) {
      console.error(`Error replying to email ${emailId}:`, error);
      throw new Error(`Failed to reply to email: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Forward an email to recipients
   * @param emailId ID of the email to forward
   * @param message Forward message content
   * @param toRecipients Recipients to forward to
   * @returns Boolean indicating success
   */
  async forwardEmail(
    emailId: string, 
    message: string, 
    toRecipients: Array<{ emailAddress: { address: string; name?: string } }>
  ): Promise<boolean> {
    try {
      const client = await this.authService.getAuthenticatedClient();
      
      // Send forward
      await client.api(`/me/messages/${emailId}/forward`).post({
        comment: message,
        toRecipients: toRecipients
      });
      
      return true;
    } catch (error) {
      console.error(`Error forwarding email ${emailId}:`, error);
      throw new Error(`Failed to forward email: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Move an email to a different folder
   * @param emailId ID of the email to move
   * @param destinationFolderId ID of the destination folder
   * @returns The moved email
   */
  async moveEmail(emailId: string, destinationFolderId: string): Promise<EmailMessage> {
    try {
      const client = await this.authService.getAuthenticatedClient();
      
      // Move the email
      const result = await client.api(`/me/messages/${emailId}/move`).post({
        destinationId: destinationFolderId
      });
      
      if (!result) {
        throw new Error(`Failed to move email: No response received`);
      }
      
      return {
        id: result.id,
        shortId: TypeCompat.generateShortId(result.id, EntityType.Email),
        subject: result.subject || '',
        from: result.from || { emailAddress: { address: '', name: '' } },
        toRecipients: result.toRecipients || [],
        ccRecipients: result.ccRecipients || [],
        bccRecipients: result.bccRecipients || [],
        receivedDateTime: result.receivedDateTime || new Date().toISOString(),
        hasAttachments: result.hasAttachments || false,
        bodyPreview: result.bodyPreview || '',
        importance: result.importance || 'normal',
        isRead: result.isRead || false,
        folderId: destinationFolderId
      };
    } catch (error) {
      console.error(`Error moving email ${emailId} to folder ${destinationFolderId}:`, error);
      throw new Error(`Failed to move email: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Copy an email to a different folder
   * @param emailId ID of the email to copy
   * @param destinationFolderId ID of the destination folder
   * @returns The copied email
   */
  async copyEmail(emailId: string, destinationFolderId: string): Promise<EmailMessage> {
    try {
      const client = await this.authService.getAuthenticatedClient();
      
      // Copy the email
      const result = await client.api(`/me/messages/${emailId}/copy`).post({
        destinationId: destinationFolderId
      });
      
      if (!result) {
        throw new Error(`Failed to copy email: No response received`);
      }
      
      return {
        id: result.id,
        shortId: TypeCompat.generateShortId(result.id, EntityType.Email),
        subject: result.subject || '',
        from: result.from || { emailAddress: { address: '', name: '' } },
        toRecipients: result.toRecipients || [],
        ccRecipients: result.ccRecipients || [],
        bccRecipients: result.bccRecipients || [],
        receivedDateTime: result.receivedDateTime || new Date().toISOString(),
        hasAttachments: result.hasAttachments || false,
        bodyPreview: result.bodyPreview || '',
        importance: result.importance || 'normal',
        isRead: result.isRead || false,
        folderId: destinationFolderId
      };
    } catch (error) {
      console.error(`Error copying email ${emailId} to folder ${destinationFolderId}:`, error);
      throw new Error(`Failed to copy email: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Mark an email as read or unread
   * @param emailId ID of the email to update
   * @param isRead Whether the email should be marked as read
   * @returns Boolean indicating success
   */
  async markAsRead(emailId: string, isRead: boolean): Promise<boolean> {
    try {
      const client = await this.authService.getAuthenticatedClient();
      
      // Update isRead property
      await client.api(`/me/messages/${emailId}`).patch({
        isRead: isRead
      });
      
      return true;
    } catch (error) {
      console.error(`Error marking email ${emailId} as ${isRead ? 'read' : 'unread'}:`, error);
      throw new Error(`Failed to mark email as ${isRead ? 'read' : 'unread'}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Delete an email
   * @param emailId ID of the email to delete
   * @returns Boolean indicating success
   */
  async deleteEmail(emailId: string): Promise<boolean> {
    try {
      const client = await this.authService.getAuthenticatedClient();
      
      // Delete the email
      await client.api(`/me/messages/${emailId}`).delete();
      
      return true;
    } catch (error) {
      console.error(`Error deleting email ${emailId}:`, error);
      throw new Error(`Failed to delete email: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }
}
EOF

      console.log(`BCC: ${bccRecipients}`);
    }
    
    console.log(`ID: ${draft.shortId || draft.id}`);
    
    console.log('\nBody:');
    if (draft.body && draft.body.content) {
      if (draft.body.contentType === 'html') {
        console.log('(HTML content - rendered version:)');
        // Simple HTML to text conversion
        const text = draft.body.content
          .replace(/<[^>]*>/g, '')
          .replace(/&nbsp;/g, ' ')
          .replace(/&lt;/g, '<')
          .replace(/&gt;/g, '>')
          .replace(/&amp;/g, '&');
        console.log(text);
      } else {
        console.log(draft.body.content);
      }
    } else {
      console.log('(No body content)');
    }
  } catch (error) {
    console.error(chalk.red('Error getting draft:'), error instanceof Error ? error.message : error);
  }
}

/**
 * Command to update an existing draft email
 */
export async function updateDraftCommand(draftId: string, options: any): Promise<void> {
  try {
    const draftService = getDraftService();
    
    // Build update payload based on provided options
    const updatePayload: Partial<DraftMessage> = {};
    
    if (options.subject) {
      updatePayload.subject = options.subject;
    }
    
    if (options.body) {
      updatePayload.body = {
        contentType: options.bodyType || 'text',
        content: options.body
      };
    }
    
    if (options.to) {
      updatePayload.toRecipients = options.to.split(',').map((email: string) => ({
        emailAddress: {
          address: email.trim()
        }
      }));
    }
    
    if (options.cc) {
      updatePayload.ccRecipients = options.cc.split(',').map((email: string) => ({
        emailAddress: {
          address: email.trim()
        }
      }));
    }
    
    if (options.bcc) {
      updatePayload.bccRecipients = options.bcc.split(',').map((email: string) => ({
        emailAddress: {
          address: email.trim()
        }
      }));
    }
    
    const result = await draftService.updateDraft(draftId, updatePayload);
    console.log(chalk.green('Draft updated successfully:'));
    console.log(`ID: ${result.id}`);
    console.log(`Subject: ${result.subject}`);
  } catch (error) {
    console.error(chalk.red('Error updating draft:'), error instanceof Error ? error.message : error);
  }
}

/**
 * Command to send a draft email
 */
export async function sendDraftCommand(draftId: string, options: any): Promise<void> {
  try {
    const draftService = getDraftService();
    const result = await draftService.sendDraft(draftId);
    
    if (result) {
      console.log(chalk.green(`Draft with ID ${draftId} sent successfully.`));
    } else {
      console.log(chalk.yellow(`Draft with ID ${draftId} could not be sent.`));
    }
  } catch (error) {
    console.error(chalk.red('Error sending draft:'), error instanceof Error ? error.message : error);
  }
}

/**
 * Command to delete a draft email
 */
export async function deleteDraftCommand(draftId: string, options: any): Promise<void> {
  try {
    const draftService = getDraftService();
    const result = await draftService.deleteDraft(draftId);
    
    if (result) {
      console.log(chalk.green(`Draft with ID ${draftId} deleted successfully.`));
    } else {
      console.log(chalk.yellow(`Draft with ID ${draftId} could not be deleted.`));
    }
  } catch (error) {
    console.error(chalk.red('Error deleting draft:'), error instanceof Error ? error.message : error);
  }
}
EOF

# Fix calendar.ts to handle date formatting correctly
cat > src/cli/commands/calendar.ts << 'EOF'
import { Command } from 'commander';
import { getCalendarService } from '../../services/adapters.fixed';
import { CalendarSearchOptions, NewCalendarEvent } from '../../models/calendar';
import chalk from 'chalk';

/**
 * Command to list all calendars
 */
export async function listCalendarsCommand(options: any): Promise<void> {
  try {
    const calendarService = getCalendarService();
    const calendars = await calendarService.getCalendars();
    
    if (!calendars || calendars.length === 0) {
      console.log('No calendars found.');
      return;
    }
    
    console.log(`Found ${calendars.length} calendars:`);
    
    calendars.forEach((calendar, index) => {
      console.log(`${index + 1}. ${chalk.bold(calendar.name)}`);
      console.log(`   ID: ${calendar.shortId || calendar.id}`);
      console.log(`   Owner: ${calendar.owner || 'Unknown'}`);
      console.log(`   Can Edit: ${calendar.canEdit ? 'Yes' : 'No'}`);
      console.log(`   Can Share: ${calendar.canShare ? 'Yes' : 'No'}`);
      console.log('');
    });
  } catch (error) {
    console.error(chalk.red('Error listing calendars:'), error instanceof Error ? error.message : error);
  }
}

/**
 * Command to get a specific calendar
 */
export async function getCalendarCommand(calendarId: string, options: any): Promise<void> {
  try {
    const calendarService = getCalendarService();
    const calendar = await calendarService.getCalendar(calendarId);
    
    if (!calendar) {
      console.log(`Calendar with ID ${calendarId} not found.`);
      return;
    }
    
    console.log(chalk.bold(`Calendar: ${calendar.name}`));
    console.log(`ID: ${calendar.id}`);
    console.log(`Short ID: ${calendar.shortId || 'N/A'}`);
    console.log(`Owner: ${calendar.owner || 'Unknown'}`);
    console.log(`Can Edit: ${calendar.canEdit ? 'Yes' : 'No'}`);
    console.log(`Can Share: ${calendar.canShare ? 'Yes' : 'No'}`);
    console.log(`Can View Private Items: ${calendar.canViewPrivateItems ? 'Yes' : 'No'}`);
  } catch (error) {
    console.error(chalk.red('Error getting calendar:'), error instanceof Error ? error.message : error);
  }
}

/**
 * Command to list events from a calendar
 */
export async function listEventsCommand(calendarId: string, options: any): Promise<void> {
  try {
    const calendarService = getCalendarService();
    
    // Build search options
    const searchOptions: CalendarSearchOptions = {};
    
    if (options.startDate) {
      // Convert string date to ISO string
      searchOptions.startDateTime = new Date(options.startDate).toISOString();
    }
    
    if (options.endDate) {
      // Convert string date to ISO string
      searchOptions.endDateTime = new Date(options.endDate).toISOString();
    }
    
    if (options.limit) {
      searchOptions.limit = parseInt(options.limit, 10);
    }
    
    const events = await calendarService.getEvents(calendarId, searchOptions);
    
    if (!events || events.length === 0) {
      console.log('No events found.');
      return;
    }
    
    console.log(`Found ${events.length} events:`);
    
    events.forEach((event, index) => {
      console.log(`${index + 1}. ${chalk.bold(event.subject || '(No subject)')}`);
      
      const startDate = new Date(
        typeof event.start === 'string' ? event.start : event.start.dateTime
      );
      const endDate = new Date(
        typeof event.end === 'string' ? event.end : event.end.dateTime
      );
      
      console.log(`   Date: ${startDate.toLocaleDateString()} ${event.isAllDay ? '(All day)' : startDate.toLocaleTimeString() + ' - ' + endDate.toLocaleTimeString()}`);
      console.log(`   Location: ${event.location || 'No location'}`);
      console.log(`   ID: ${event.shortId || event.id}`);
      
      if (event.bodyPreview) {
        console.log(`   Preview: ${event.bodyPreview.substring(0, 100)}${event.bodyPreview.length > 100 ? '...' : ''}`);
      }
      
      console.log('');
    });
  } catch (error) {
    console.error(chalk.red('Error listing events:'), error instanceof Error ? error.message : error);
  }
}

/**
 * Command to get a specific event
 */
export async function getEventCommand(calendarId: string, eventId: string, options: any): Promise<void> {
  try {
    const calendarService = getCalendarService();
    const event = await calendarService.getEvent(calendarId, eventId);
    
    if (!event) {
      console.log(`Event with ID ${eventId} not found in calendar ${calendarId}.`);
      return;
    }
    
    console.log(chalk.bold(`Subject: ${event.subject || '(No subject)'}`));
    
    const startDate = new Date(
      typeof event.start === 'string' ? event.start : event.start.dateTime
    );
    const endDate = new Date(
      typeof event.end === 'string' ? event.end : event.end.dateTime
    );
    
    console.log(`Date: ${startDate.toLocaleDateString()} ${event.isAllDay ? '(All day)' : startDate.toLocaleTimeString() + ' - ' + endDate.toLocaleTimeString()}`);
    console.log(`Location: ${event.location || 'No location'}`);
    console.log(`Is Online Meeting: ${event.isOnlineMeeting ? 'Yes' + (event.onlineMeetingUrl ? ' (' + event.onlineMeetingUrl + ')' : '') : 'No'}`);
    console.log(`ID: ${event.id}`);
    console.log(`Short ID: ${event.shortId || 'N/A'}`);
    
    if (event.organizer) {
      console.log(`Organizer: ${event.organizer.emailAddress?.name || event.organizer.emailAddress?.address || 'Unknown'}`);
    }
    
    if (event.attendees && event.attendees.length > 0) {
      console.log('\nAttendees:');
      event.attendees.forEach((attendee, index) => {
        console.log(`${index + 1}. ${attendee.emailAddress?.name || attendee.emailAddress?.address || 'Unknown'} (${attendee.type || 'required'})`);
      });
    }
    
    console.log('\nBody:');
    if (event.body && event.body.content) {
      if (event.body.contentType === 'html') {
        console.log('(HTML content - rendered version:)');
        // Simple HTML to text conversion
        const text = event.body.content
          .replace(/<[^>]*>/g, '')
          .replace(/&nbsp;/g, ' ')
          .replace(/&lt;/g, '<')
          .replace(/&gt;/g, '>')
          .replace(/&amp;/g, '&');
        console.log(text);
      } else {
        console.log(event.body.content);
      }
    } else {
      console.log('(No body content)');
    }
  } catch (error) {
    console.error(chalk.red('Error getting event:'), error instanceof Error ? error.message : error);
  }
}

/**
 * Command to create a new event
 */
export async function createEventCommand(calendarId: string, options: any): Promise<void> {
  try {
    const calendarService = getCalendarService();
    
    // Parse start and end dates
    const startDate = options.start ? new Date(options.start) : new Date();
    const endDate = options.end ? new Date(options.end) : new Date(startDate.getTime() + 3600000); // Default to 1 hour after start
    
    // Create event payload
    const newEvent: NewCalendarEvent = {
      subject: options.subject || 'New Event',
      start: {
        dateTime: startDate.toISOString(),
        timeZone: options.timeZone || 'UTC'
      },
      end: {
        dateTime: endDate.toISOString(),
        timeZone: options.timeZone || 'UTC'
      },
      isAllDay: options.allDay || false,
      isOnlineMeeting: options.onlineMeeting || false,
      location: options.location || '',
      body: options.body || '',
      bodyContentType: options.bodyType || 'text',
      timeZone: options.timeZone || 'UTC' // Required timeZone property
    };
    
    // Add attendees if provided
    if (options.attendees) {
      newEvent.attendees = options.attendees.split(',').map((email: string) => email.trim());
    }
    
    const result = await calendarService.createEvent(calendarId, newEvent);
    
    console.log(chalk.green('Event created successfully:'));
    console.log(`ID: ${result.id}`);
    console.log(`Subject: ${result.subject}`);
    console.log(`Start: ${new Date(
      typeof result.start === 'string' ? result.start : result.start.dateTime
    ).toLocaleString()}`);
    console.log(`End: ${new Date(
      typeof result.end === 'string' ? result.end : result.end.dateTime
    ).toLocaleString()}`);
  } catch (error) {
    console.error(chalk.red('Error creating event:'), error instanceof Error ? error.message : error);
  }
}

/**
 * Command to update an existing event
 */
export async function updateEventCommand(calendarId: string, eventId: string, options: any): Promise<void> {
  try {
    const calendarService = getCalendarService();
    
    // Build update payload based on provided options
    const updatePayload: any = {};
    
    if (options.subject) {
      updatePayload.subject = options.subject;
    }
    
    if (options.location) {
      updatePayload.location = options.location;
    }
    
    if (options.body) {
      updatePayload.body = {
        content: options.body,
        contentType: options.bodyType || 'text'
      };
      updatePayload.bodyContentType = options.bodyType || 'text';
    }
    
    if (options.start) {
      const startDate = new Date(options.start);
      updatePayload.start = {
        dateTime: startDate.toISOString(),
        timeZone: options.timeZone || 'UTC'
      };
    }
    
    if (options.end) {
      const endDate = new Date(options.end);
      updatePayload.end = {
        dateTime: endDate.toISOString(),
        timeZone: options.timeZone || 'UTC'
      };
    }
    
    if (options.timeZone) {
      updatePayload.timeZone = options.timeZone;
    }
    
    if (typeof options.allDay === 'boolean') {
      updatePayload.isAllDay = options.allDay;
    }
    
    if (typeof options.onlineMeeting === 'boolean') {
      updatePayload.isOnlineMeeting = options.onlineMeeting;
    }
    
    if (options.attendees) {
      updatePayload.attendees = options.attendees.split(',').map((email: string) => email.trim());
    }
    
    const result = await calendarService.updateEvent(calendarId, eventId, updatePayload);
    
    console.log(chalk.green('Event updated successfully:'));
    console.log(`ID: ${result.id}`);
    console.log(`Subject: ${result.subject}`);
    console.log(`Start: ${new Date(
      typeof result.start === 'string' ? result.start : result.start.dateTime
    ).toLocaleString()}`);
    console.log(`End: ${new Date(
      typeof result.end === 'string' ? result.end : result.end.dateTime
    ).toLocaleString()}`);
  } catch (error) {
    console.error(chalk.red('Error updating event:'), error instanceof Error ? error.message : error);
  }
}

/**
 * Command to delete an event
 */
export async function deleteEventCommand(calendarId: string, eventId: string, options: any): Promise<void> {
  try {
    const calendarService = getCalendarService();
    const result = await calendarService.deleteEvent(calendarId, eventId);
    
    if (result) {
      console.log(chalk.green(`Event with ID ${eventId} deleted successfully from calendar ${calendarId}.`));
    } else {
      console.log(chalk.yellow(`Event with ID ${eventId} could not be deleted from calendar ${calendarId}.`));
    }
  } catch (error) {
    console.error(chalk.red('Error deleting event:'), error instanceof Error ? error.message : error);
  }
}
EOF

# Fix CLI utils command
cat > src/cli/commands/utils.ts << 'EOF'
import { Command } from 'commander';
import chalk from 'chalk';
import * as cheerio from 'cheerio';

/**
 * Command to convert HTML content to plain text
 */
export async function convertHtmlCommand(options: any): Promise<void> {
  try {
    const { html } = options;
    
    if (!html) {
      console.error(chalk.red('Error: HTML content is required.'));
      console.log('Usage: outlook utils convert-html --html "<html>...</html>"');
      return;
    }
    
    // Use cheerio to parse and extract text
    const $ = cheerio.load(html);
    
    // Remove script and style elements
    $('script, style').remove();
    
    // Get text and normalize whitespace
    let text = $('body').text().trim();
    text = text.replace(/\s+/g, ' ');
    
    console.log(chalk.green('Converted Plain Text:'));
    console.log(text);
  } catch (error) {
    console.error(chalk.red('Error converting HTML:'), error instanceof Error ? error.message : error);
  }
}
EOF

# Fix CLI index.ts with proper command parameters
cat > src/cli/index.ts << 'EOF'
#!/usr/bin/env node

import { Command } from 'commander';
import * as dotenv from 'dotenv';
import * as authCommands from './commands/auth';
import * as emailCommands from './commands/email';
import * as folderCommands from './commands/folder';
import * as draftCommands from './commands/draft';
import * as calendarCommands from './commands/calendar';
import * as utilCommands from './commands/utils';

// Load environment variables
dotenv.config();

const program = new Command();

program
  .name('outlook')
  .description('Outlook CLI - Access Microsoft Outlook via command line')
  .version('1.1.0');

// Auth Commands
program
  .command('auth')
  .description('Authenticate with Microsoft Graph API')
  .action(() => authCommands.authenticateCommand());

// Email Commands
program
  .command('email:list')
  .description('List emails in a folder')
  .option('-f, --folder <folder>', 'Folder ID or path (default: inbox)', 'inbox')
  .option('-l, --limit <limit>', 'Maximum number of emails to return')
  .option('-s, --search <search>', 'Search term to filter emails')
  .option('-o, --order-by <orderBy>', 'Field to order by (receivedDateTime, subject, etc.)')
  .action(options => emailCommands.listEmailsCommand(options));

program
  .command('email:get <emailId>')
  .description('Get a specific email by ID')
  .action((emailId, options) => emailCommands.getEmailCommand(emailId, options));

program
  .command('email:send')
  .description('Send a new email')
  .requiredOption('-t, --to <recipients>', 'Comma-separated list of recipients')
  .option('-c, --cc <recipients>', 'Comma-separated list of CC recipients')
  .option('-b, --bcc <recipients>', 'Comma-separated list of BCC recipients')
  .requiredOption('-s, --subject <subject>', 'Email subject')
  .requiredOption('--body <body>', 'Email body content')
  .option('--body-type <type>', 'Body content type (text or html)', 'text')
  .action(options => emailCommands.sendEmailCommand(options));

program
  .command('email:reply <emailId>')
  .description('Reply to an email')
  .requiredOption('--body <body>', 'Reply message')
  .option('--reply-all', 'Reply to all recipients', false)
  .action((emailId, options) => emailCommands.replyEmailCommand(emailId, options));

program
  .command('email:forward <emailId>')
  .description('Forward an email')
  .requiredOption('-t, --to <recipients>', 'Comma-separated list of recipients')
  .requiredOption('--body <body>', 'Forward message')
  .action((emailId, options) => emailCommands.forwardEmailCommand(emailId, options));

program
  .command('email:move <emailId>')
  .description('Move an email to a different folder')
  .requiredOption('-f, --folder <folderId>', 'Destination folder ID or path')
  .action((emailId, options) => emailCommands.moveEmailCommand(emailId, options));

program
  .command('email:copy <emailId>')
  .description('Copy an email to a different folder')
  .requiredOption('-f, --folder <folderId>', 'Destination folder ID or path')
  .action((emailId, options) => emailCommands.copyEmailCommand(emailId, options));

program
  .command('email:mark-read <emailId>')
  .description('Mark an email as read or unread')
  .option('--unread', 'Mark as unread (default is to mark as read)', false)
  .action((emailId, options) => emailCommands.markReadCommand(emailId, options));

program
  .command('email:delete <emailId>')
  .description('Delete an email')
  .action((emailId, options) => emailCommands.deleteEmailCommand(emailId, options));

// Draft Commands
program
  .command('draft:create')
  .description('Create a new draft email')
  .option('-t, --to <recipients>', 'Comma-separated list of recipients')
  .option('-c, --cc <recipients>', 'Comma-separated list of CC recipients')
  .option('-b, --bcc <recipients>', 'Comma-separated list of BCC recipients')
  .option('-s, --subject <subject>', 'Email subject')
  .option('--body <body>', 'Email body content')
  .option('--body-type <type>', 'Body content type (text or html)', 'text')
  .action(options => draftCommands.createDraftCommand(options));

program
  .command('draft:list')
  .description('List all draft emails')
  .action((options) => draftCommands.listDraftsCommand(options));

program
  .command('draft:get <draftId>')
  .description('Get a specific draft by ID')
  .action((draftId, options) => draftCommands.getDraftCommand(draftId, options));

program
  .command('draft:update <draftId>')
  .description('Update a draft email')
  .option('-t, --to <recipients>', 'Comma-separated list of recipients')
  .option('-c, --cc <recipients>', 'Comma-separated list of CC recipients')
  .option('-b, --bcc <recipients>', 'Comma-separated list of BCC recipients')
  .option('-s, --subject <subject>', 'Email subject')
  .option('--body <body>', 'Email body content')
  .option('--body-type <type>', 'Body content type (text or html)')
  .action((draftId, options) => draftCommands.updateDraftCommand(draftId, options));

program
  .command('draft:send <draftId>')
  .description('Send a draft email')
  .action((draftId, options) => draftCommands.sendDraftCommand(draftId, options));

program
  .command('draft:delete <draftId>')
  .description('Delete a draft email')
  .action((draftId, options) => draftCommands.deleteDraftCommand(draftId, options));

// Folder Commands
program
  .command('folder:list')
  .description('List all mail folders')
  .option('-e, --email <email>', 'User email address (default: current user)')
  .action(options => folderCommands.listFoldersCommand(options));

program
  .command('folder:get <folderIdOrPath>')
  .description('Get a specific folder by ID or path')
  .action((folderIdOrPath, options) => folderCommands.getFolderCommand(folderIdOrPath, options));

program
  .command('folder:create <name>')
  .description('Create a new folder')
  .option('-p, --parent <parentFolderIdOrPath>', 'Parent folder ID or path (default: root)')
  .option('-e, --email <email>', 'User email address (default: current user)')
  .action((name, options) => folderCommands.createFolderCommand({name, ...options}));

program
  .command('folder:rename <folderIdOrPath> <newName>')
  .description('Rename a folder')
  .action((folderIdOrPath, newName, options) => folderCommands.renameFolderCommand({folderIdOrPath, newName, ...options}));

program
  .command('folder:move <folderIdOrPath> <destinationParentFolderIdOrPath>')
  .description('Move a folder to a different parent folder')
  .action((folderIdOrPath, destinationParentFolderIdOrPath, options) => 
    folderCommands.moveFolderCommand({folderIdOrPath, destinationParentFolderIdOrPath, ...options}));

program
  .command('folder:copy <folderIdOrPath> <destinationParentFolderIdOrPath>')
  .description('Copy a folder to a different parent folder')
  .action((folderIdOrPath, destinationParentFolderIdOrPath, options) => 
    folderCommands.copyFolderCommand({folderIdOrPath, destinationParentFolderIdOrPath, ...options}));

program
  .command('folder:delete <folderIdOrPath>')
  .description('Delete a folder')
  .action((folderIdOrPath, options) => folderCommands.deleteFolderCommand(folderIdOrPath, options));

// Calendar Commands
program
  .command('calendar:list')
  .description('List all calendars')
  .action(options => calendarCommands.listCalendarsCommand(options));

program
  .command('calendar:get <calendarId>')
  .description('Get a specific calendar by ID')
  .action((calendarId, options) => calendarCommands.getCalendarCommand(calendarId, options));

program
  .command('calendar:events <calendarId>')
  .description('List events from a calendar')
  .option('--start <date>', 'Start date for events (format: YYYY-MM-DD or ISO string)')
  .option('--end <date>', 'End date for events (format: YYYY-MM-DD or ISO string)')
  .option('-l, --limit <limit>', 'Maximum number of events to return')
  .action((calendarId, options) => calendarCommands.listEventsCommand(calendarId, options));

program
  .command('calendar:event:get <calendarId> <eventId>')
  .description('Get a specific event by ID')
  .action((calendarId, eventId, options) => calendarCommands.getEventCommand(calendarId, eventId, options));

program
  .command('calendar:event:create <calendarId>')
  .description('Create a new event')
  .requiredOption('-s, --subject <subject>', 'Event subject')
  .option('--start <datetime>', 'Start date and time (ISO format or YYYY-MM-DD HH:MM)')
  .option('--end <datetime>', 'End date and time (ISO format or YYYY-MM-DD HH:MM)')
  .option('-l, --location <location>', 'Event location')
  .option('-b, --body <body>', 'Event body content')
  .option('--body-type <type>', 'Body content type (text or html)', 'text')
  .option('--time-zone <zone>', 'Time zone (e.g., UTC, America/New_York)', 'UTC')
  .option('--all-day', 'All-day event', false)
  .option('--online-meeting', 'Create as online meeting', false)
  .option('-a, --attendees <emails>', 'Comma-separated list of attendee emails')
  .action((calendarId, options) => calendarCommands.createEventCommand(calendarId, options));

program
  .command('calendar:event:update <calendarId> <eventId>')
  .description('Update an existing event')
  .option('-s, --subject <subject>', 'Event subject')
  .option('--start <datetime>', 'Start date and time (ISO format or YYYY-MM-DD HH:MM)')
  .option('--end <datetime>', 'End date and time (ISO format or YYYY-MM-DD HH:MM)')
  .option('-l, --location <location>', 'Event location')
  .option('-b, --body <body>', 'Event body content')
  .option('--body-type <type>', 'Body content type (text or html)')
  .option('--time-zone <zone>', 'Time zone (e.g., UTC, America/New_York)')
  .option('--all-day <boolean>', 'All-day event (true or false)')
  .option('--online-meeting <boolean>', 'Is online meeting (true or false)')
  .option('-a, --attendees <emails>', 'Comma-separated list of attendee emails')
  .action((calendarId, eventId, options) => calendarCommands.updateEventCommand(calendarId, eventId, options));

program
  .command('calendar:event:delete <calendarId> <eventId>')
  .description('Delete an event')
  .action((calendarId, eventId, options) => calendarCommands.deleteEventCommand(calendarId, eventId, options));

// Utility Commands
program
  .command('utils:convert-html')
  .description('Convert HTML to plain text')
  .requiredOption('--html <html>', 'HTML content to convert')
  .action(options => utilCommands.convertHtmlCommand(options));

program.parse(process.argv);
EOF

# Step 7: Final Verification and Application
print_step "7" "Final Verification and Application"

# Make the script executable
chmod +x apply_all_fixes.sh

# Create a verification function
verify_build() {
  echo -e "${YELLOW}Verifying build...${NC}"
  
  # Run TypeScript compiler to check for errors
  npm run build

  if [ $? -eq 0 ]; then
    echo -e "${GREEN}Build successful! All TypeScript errors have been fixed.${NC}"
    return 0
  else
    echo -e "${RED}Build failed. Some TypeScript errors still remain.${NC}"
    return 1
  }
}

# Apply all modified files
apply_fixes() {
  # Replace the original files with the fixed versions where necessary
  cp src/services/type_compatibility_fixed.ts src/services/type_compatibility.ts
  cp src/services/adapters.fixed.ts src/services/adapters.ts
  
  echo -e "${GREEN}Successfully applied all fixes!${NC}"
}

# Create a clean-up function
cleanup() {
  echo -e "${YELLOW}Cleaning up temporary files...${NC}"
  
  # Remove any temporary files
  # (commented out since we keep backups for safety)
  # rm -rf temp_backup
  
  echo -e "${GREEN}Cleanup complete.${NC}"
}

# Main execution
main() {
  echo -e "${GREEN}===== MCP Outlook TypeScript Fix Script =====${NC}"
  echo -e "${GREEN}Starting fixes at $(date)${NC}"
  echo -e "${YELLOW}Creating backups in: $BACKUP_DIR${NC}"
  
  # Apply all fixes
  apply_fixes
  
  # Verify the build
  verify_build
  
  # Clean up temporary files
  cleanup
  
  echo -e "${GREEN}===== Fix Script Completed =====${NC}"
  
  # Recommendations
  echo -e "${YELLOW}Recommendations for further action:${NC}"
  echo "1. Test each service with real data to verify functionality"
  echo "2. Update the documentation to reflect the new interface implementations"
  echo "3. Consider writing additional unit tests for the fixed components"
  echo "4. Address any remaining CLI command issues that couldn't be fixed automatically"
}

# Run the main function
main
