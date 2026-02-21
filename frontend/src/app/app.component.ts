import { Component } from '@angular/core';
import { TimelapseMenuComponent } from './components/timelapse-menu/timelapse-menu.component';
import { TimelapseLibraryComponent } from './components/timelapse-library/timelapse-library.component';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
  imports: [TimelapseMenuComponent, TimelapseLibraryComponent],
})
export class AppComponent {
  
}
