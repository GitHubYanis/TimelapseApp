import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { DropdownComponent, DropdownOption } from './components/dropdown/dropdown.component';

interface TimelapseSettings {
  frequency: DropdownOption;
  duration: DropdownOption;
  resolution: DropdownOption;
}

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
  imports: [DropdownComponent],
})
export class AppComponent {
  timestamp = null;

  frequencyOptions: DropdownOption[] = [
    { label: '5 seconds', value: 5 },
    { label: '30 seconds', value: 30 },
    { label: '1 minute', value: 60 },
    { label: '1 heure', value: 3600 },
    { label: '1 jour', value: 86400 },
    { label: '2 jours', value: 172800 },
    { label: '1 week', value: 604800 }
  ];

  durationOptions: DropdownOption[] = [
    { label: '5 min', value: 300 },
    { label: '15 min', value: 900 },
    { label: '60 min', value: 3600 },
    { label: '1 day', value: 86400 },
    { label: '1 week', value: 604800 },
    { label: '1 month', value: 2628000 },
  ];

  resolutionOptions: DropdownOption[] = [
    // { label: '1920x1080', value: '1920x1080' },
    // { label: '1280x720', value: '1280x720' }, Not working
    { label: '640x480', value: '640x480' },
  ];

  settings: TimelapseSettings = {
    frequency: { label: '5 seconds', value: 5 },
    duration: { label: '5 min', value: 300 },
    resolution: { label: '640x480', value: '640x480' },
  };

  running = false;
  endDate: Date | null = null;
  error: string | null = null;
  frameNumber: string = '?';

  constructor(private http: HttpClient) {}

  getLatestFrameInfo() {
    this.http
    .get<any>('http://localhost:8000/timelapse/frame-info').subscribe({
      next: (response) => {
        this.frameNumber = response.frames_taken;

        if (response.latest_frame_time) {
          this.timestamp = response.latest_frame_time; // forces image refresh
        }
      },
      error: (err) => {
        this.error =
          'Failed to get timelapse status: ' +
          (err.error?.detail || err.message);
      },
    });
  }

  onSettingChange(key: keyof TimelapseSettings, option: DropdownOption) {
    this.settings[key] = option;
  }

  get expectedFrames(): number | null {
    return Math.floor(this.settings.duration.value as number / (this.settings.frequency.value as number));
  }

  get isFrequencyTooHigh(): boolean {
    return (this.settings.frequency.value as number) > (this.settings.duration.value as number);
  }

  start() {
    this.error = null;
    const payload = {
      frequency: this.settings.frequency.value,
      duration: this.settings.duration.value,
      resolution: this.settings.resolution.value,
    };

    this.http.post('http://localhost:8000/timelapse/start', payload).subscribe({
      next: () => {
        this.endDate = new Date(Date.now() + (this.settings.duration.value as number) * 1000);
        this.running = true;
      },
      error: (err) => {
        this.error = 'Failed to start timelapse: ' + (err.error?.detail || err.message);
      }
    });
  }

  stop() {
    this.error = null;

    this.http.post('http://localhost:8000/timelapse/stop', {}).subscribe({
      next: () => {
        this.running = false;
        this.endDate = null;
      },
      error: (err) => {
        this.error = 'Failed to stop timelapse: ' + (err.error?.detail || err.message);
        this.running = false;
      }
    });
  }
}
